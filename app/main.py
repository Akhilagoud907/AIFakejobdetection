import time
import os
import io
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse, PlainTextResponse
import logging
import json
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from app.models.inference import ModelService
from app.storage.db import (
    init_db,
    insert_flag,
    insert_prediction_event,
    hash_ip,
    list_flagged_posts,
    update_flag_status,
    metrics_summary,
    fetch_flagged_posts,
    fetch_prediction_events,
    prediction_trend,
    recent_prediction_activity,
    insert_audit_log,
)
from app.services.retrain import run_retrain, list_versions, rollback
from app.services.notify import send_email
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import redis
from rq import Queue
from app.auth.firebase import verify_id_token, require_admin_claim, configured as firebase_configured

APP_VERSION = "1.0.0"

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Fake Job Detection API", version=APP_VERSION)

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(404)
async def not_found_handler(_, __):
    return PlainTextResponse("Not found", status_code=404)


@app.exception_handler(500)
async def server_error_handler(_, __):
    return PlainTextResponse("Something went wrong. Please try again later.", status_code=500)

# CORS: allow localhost and file-based frontends by default
cors_origins = os.getenv("CORS_ALLOW_ORIGINS")
allowed_origins = [o.strip() for o in cors_origins.split(",") if o.strip()] if cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global singleton service
model_service: Optional[ModelService] = None
retrain_state = {"status": "idle"}
rq_queue: Optional[Queue] = None


class PredictRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=20000)
    company: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    salary: Optional[str] = Field(None, max_length=200)

class PredictResponse(BaseModel):
    result: str
    confidence_percent: float
    processing_time_ms: int
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    model_ready: bool
    version: str
    auth_ready: bool

class ModelInfoResponse(BaseModel):
    model: str
    version: str
    metrics: dict
    vectorizer: dict
    last_loaded: str

class FlagRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=20000)
    reason: str = Field(..., description="Why flagged (e.g., 'suspicious_contact', 'too_good_to_be_true', 'phishing')")
    comments: Optional[str] = Field(None, max_length=2000)
    user_email: Optional[str] = Field(None, max_length=200)

class FlagResponse(BaseModel):
    status: str
    id: int
    timestamp: str


class AdminMetricsResponse(BaseModel):
    total_predictions: int
    fake_predictions: int
    real_predictions: int
    total_flags: int
    pending_flags: int


class FlaggedItem(BaseModel):
    id: int
    description: str
    reason: str
    comments: Optional[str]
    user_email: Optional[str]
    prediction: int
    confidence: str
    processing_time_ms: int
    timestamp: str
    model: str
    status: str
    admin_notes: Optional[str]
    validated_label: Optional[int]


class FlaggedListResponse(BaseModel):
    items: List[FlaggedItem]


class TrendPoint(BaseModel):
    day: str
    total: int
    fake: int


class TrendResponse(BaseModel):
    points: List[TrendPoint]


class ActivityItem(BaseModel):
    id: int
    timestamp: str
    prediction: int
    confidence: float
    processing_time_ms: int
    source: Optional[str]
    model: Optional[str]


class ActivityResponse(BaseModel):
    items: List[ActivityItem]


class FlagStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None
    validated_label: Optional[int] = None


def _parse_token(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    return authorization.split(" ", 1)[1].strip()


async def current_user(token: str = Depends(_parse_token)):
    return verify_id_token(token)


async def admin_user(claims=Depends(current_user)):
    return require_admin_claim(claims)


@app.on_event("startup")
async def startup_event():
    global model_service
    init_db()   
    model_service = ModelService()
    model_service.load()
    global rq_queue
    try:
        if os.getenv("USE_RQ") == "1" and os.getenv("REDIS_URL"):
            redis_conn = redis.from_url(os.getenv("REDIS_URL"))
            rq_queue = Queue("retrain", connection=redis_conn)
            logger.info("RQ queue initialized")
    except Exception:
        rq_queue = None
        logger.warning("Failed to initialize RQ queue; falling back to in-process tasks")


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    """Serve the main frontend page"""
    return FileResponse("app/frontend/index.html")


@app.get("/admin")
async def admin():
    """Serve the admin dashboard page"""
    return FileResponse("app/frontend/admin.html")


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model_ready=model_service is not None and model_service.ready,
        version=APP_VERSION,
        auth_ready=firebase_configured(),
    )


@app.get("/model-info", response_model=ModelInfoResponse)
async def model_info():
    if not model_service or not model_service.ready:
        raise HTTPException(status_code=503, detail="Model not ready")
    info = model_service.info()
    return ModelInfoResponse(
        model=info.get("model", "unknown"),
        version=APP_VERSION,
        metrics=info.get("metrics", {}),
        vectorizer=info.get("vectorizer", {}),
        last_loaded=info.get("last_loaded", datetime.utcnow().isoformat()),
    )


@app.post("/predict", response_model=PredictResponse)
@limiter.limit("30/minute")
async def predict(req: PredictRequest, request: Request):
    if not model_service or not model_service.ready:
        raise HTTPException(status_code=503, detail="Model not ready")

    start = time.perf_counter()
    try:
        pred_label, confidence = model_service.predict(req.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Prediction error")
        raise HTTPException(status_code=500, detail="Prediction error")
    end = time.perf_counter()

    result = "Fake" if pred_label == 1 else "Real"
    resp = PredictResponse(
        result=result,
        confidence_percent=round(confidence * 100.0, 2),
        processing_time_ms=int((end - start) * 1000),
        timestamp=datetime.utcnow().isoformat(),
    )
    try:
        ip_raw = request.headers.get("x-forwarded-for") or (request.client.host if request.client else None)
        insert_prediction_event({
            "prediction": int(pred_label),
            "confidence": float(confidence),
            "processing_time_ms": resp.processing_time_ms,
            "timestamp": resp.timestamp,
            "source": "api",
            "ip_hash": hash_ip(ip_raw),
            "model": model_service.model_name or "unknown",
        })
    except Exception:
        # Do not fail the main request if logging fails
        logger.debug("Prediction event logging failed", exc_info=True)
        pass
    return resp


@app.post("/feedback/flag", response_model=FlagResponse)
@limiter.limit("20/minute")
async def flag(req: FlagRequest, request: Request):
    if not model_service or not model_service.ready:
        raise HTTPException(status_code=503, detail="Model not ready")

    # Compute a prediction for context
    start = time.perf_counter()
    pred_label, confidence = model_service.predict(req.description)
    end = time.perf_counter()

    record = {
        "description": req.description,
        "reason": req.reason,
        "comments": req.comments,
        "user_email": req.user_email,
        "prediction": int(pred_label),
        "confidence": float(confidence),
        "processing_time_ms": int((end - start) * 1000),
        "timestamp": datetime.utcnow().isoformat(),
        "model": model_service.model_name or "unknown",
    }
    new_id = insert_flag(record)
    return FlagResponse(status="saved", id=new_id, timestamp=record["timestamp"])


@app.get("/admin/metrics/summary", response_model=AdminMetricsResponse)
async def admin_metrics(claims: dict = Depends(admin_user)):
    data = metrics_summary()
    insert_audit_log(claims.get("email"), "metrics_summary", {})
    return AdminMetricsResponse(**data)


@app.get("/admin/flags", response_model=FlaggedListResponse)
async def admin_flags(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    claims: dict = Depends(admin_user),
):
    items = list_flagged_posts(limit=limit, offset=offset, status=status)
    insert_audit_log(claims.get("email"), "admin_flags_list", {"status": status, "limit": limit, "offset": offset})
    return FlaggedListResponse(items=[FlaggedItem(**i) for i in items])


@app.post("/admin/flags/{flag_id}/status")
async def admin_update_flag(flag_id: int, payload: FlagStatusUpdate, _: dict = Depends(admin_user)):
    ok = update_flag_status(flag_id, payload.status, payload.admin_notes, payload.validated_label)
    if not ok:
        raise HTTPException(status_code=404, detail="Flag not found")
    insert_audit_log(_.get("email"), "flag_update", {"id": flag_id, "status": payload.status, "validated_label": payload.validated_label})
    return {"status": "updated"}


def _csv_response(rows, headers: List[str], filename: str) -> StreamingResponse:
    def generate():
        yield ",".join(headers) + "\n"
        for row in rows:
            values = [str(row.get(h, "")) for h in headers]
            yield ",".join(values) + "\n"
    return StreamingResponse(generate(), media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


def _pdf_response(buffer: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(io.BytesIO(buffer), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@app.get("/admin/export/flags")
async def export_flags(
    start: Optional[str] = Query(None, description="ISO timestamp start"),
    end: Optional[str] = Query(None, description="ISO timestamp end"),
    claims: dict = Depends(admin_user),
):
    items = fetch_flagged_posts(start_ts=start, end_ts=end)
    insert_audit_log(claims.get("email"), "export_flags", {"start": start, "end": end})
    rows = [
        {
            "id": f.id,
            "timestamp": f.timestamp,
            "prediction": f.prediction,
            "confidence": f.confidence,
            "reason": f.reason,
            "status": getattr(f, "status", ""),
            "user_email": f.user_email or "",
            "model": f.model,
        }
        for f in items
    ]
    return _csv_response(rows, ["id", "timestamp", "prediction", "confidence", "reason", "status", "user_email", "model"], "flagged_posts.csv")


@app.get("/admin/export/predictions")
async def export_predictions(
    start: Optional[str] = Query(None, description="ISO timestamp start"),
    end: Optional[str] = Query(None, description="ISO timestamp end"),
    claims: dict = Depends(admin_user),
):
    items = fetch_prediction_events(start_ts=start, end_ts=end)
    insert_audit_log(claims.get("email"), "export_predictions", {"start": start, "end": end})
    rows = [
        {
            "id": p.id,
            "timestamp": p.timestamp,
            "prediction": p.prediction,
            "confidence": p.confidence,
            "processing_time_ms": p.processing_time_ms,
            "source": p.source,
            "model": p.model,
        }
        for p in items
    ]
    return _csv_response(rows, ["id", "timestamp", "prediction", "confidence", "processing_time_ms", "source", "model"], "predictions.csv")


@app.get("/admin/export/report.pdf")
async def export_report_pdf(
    days: int = Query(30, ge=1, le=180),
    claims: dict = Depends(admin_user),
):
    insert_audit_log(claims.get("email"), "export_report_pdf", {"days": days})
    metrics = metrics_summary()
    trend_points = prediction_trend(days=days)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Fake Job Detector — Admin Report")
    y -= 24
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Generated: {datetime.utcnow().isoformat()} (UTC)")
    y -= 24

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Summary Metrics")
    y -= 18
    c.setFont("Helvetica", 10)
    for k, v in metrics.items():
        c.drawString(50, y, f"{k.replace('_',' ').title()}: {v}")
        y -= 14

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, f"Trend (last {days} days)")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Day           Total    Fake")
    y -= 14
    for p in trend_points[-20:]:  # last 20 rows to fit page
        c.drawString(50, y, f"{p['day']}    {p['total']:>5}    {p['fake']:>5}")
        y -= 14
        if y < 60:
            c.showPage(); y = height - 50; c.setFont("Helvetica", 10)

    c.showPage()
    c.save()
    pdf_bytes = buf.getvalue()
    buf.close()
    return _pdf_response(pdf_bytes, "admin_report.pdf")


def _export_payload(start: Optional[str], end: Optional[str]):
    flags = fetch_flagged_posts(start_ts=start, end_ts=end)
    preds = fetch_prediction_events(start_ts=start, end_ts=end)
    flag_rows = [
        {
            "id": f.id,
            "timestamp": f.timestamp,
            "prediction": f.prediction,
            "confidence": f.confidence,
            "reason": f.reason,
            "status": getattr(f, "status", ""),
            "user_email": f.user_email or "",
            "model": f.model,
        }
        for f in flags
    ]
    pred_rows = [
        {
            "id": p.id,
            "timestamp": p.timestamp,
            "prediction": p.prediction,
            "confidence": p.confidence,
            "processing_time_ms": p.processing_time_ms,
            "source": p.source,
            "model": p.model,
        }
        for p in preds
    ]
    return flag_rows, pred_rows


def _make_csv(rows, headers):
    output = io.StringIO()
    output.write(",".join(headers) + "\n")
    for row in rows:
        values = [str(row.get(h, "")) for h in headers]
        output.write(",".join(values) + "\n")
    return output.getvalue().encode("utf-8")


@app.post("/admin/export/email")
async def export_and_email(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    claims: dict = Depends(admin_user),
    background_tasks: BackgroundTasks = None,
):
    def task():
        flag_rows, pred_rows = _export_payload(start, end)
        metrics = metrics_summary()
        pdf_resp = app.dependency_overrides.get("__pdf__") if False else None
        pdf_buffer = None
        # reuse PDF generator
        try:
            pdf_resp = export_report_pdf.__wrapped__(days=30, _=None)  # type: ignore
        except Exception:
            pdf_resp = None
        pdf_bytes = None
        if isinstance(pdf_resp, StreamingResponse):
            # not straightforward to grab body; regenerate directly
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=letter)
            width, height = letter
            y = height - 50
            c.setFont("Helvetica-Bold", 16)
            c.drawString(40, y, "Fake Job Detector — Admin Report")
            y -= 24
            c.setFont("Helvetica", 10)
            c.drawString(40, y, f"Generated: {datetime.utcnow().isoformat()} (UTC)")
            y -= 24
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Summary Metrics")
            y -= 18
            c.setFont("Helvetica", 10)
            for k, v in metrics.items():
                c.drawString(50, y, f"{k.replace('_',' ').title()}: {v}")
                y -= 14
            c.showPage(); c.save(); pdf_bytes = buf.getvalue(); buf.close()
        flags_csv = _make_csv(flag_rows, ["id","timestamp","prediction","confidence","reason","status","user_email","model"])
        preds_csv = _make_csv(pred_rows, ["id","timestamp","prediction","confidence","processing_time_ms","source","model"])
        attachments = [
            ("flagged_posts.csv", flags_csv, "text/csv"),
            ("predictions.csv", preds_csv, "text/csv"),
        ]
        if pdf_bytes:
            attachments.append(("admin_report.pdf", pdf_bytes, "application/pdf"))
        send_email("Scheduled export", "See attached exports.", attachments)

    if background_tasks is not None:
        background_tasks.add_task(task)
    else:
        task()
    insert_audit_log(claims.get("email"), "export_email", {"start": start, "end": end})
    return {"status": "queued"}


def _notify_retrain(status: str, detail: dict):
    subject = f"Retrain {status}"
    body = json.dumps(detail, indent=2)
    send_email(subject, body)


def _background_retrain():
    global retrain_state
    retrain_state = {"status": "running", "started_at": datetime.utcnow().isoformat()}
    try:
        result = run_retrain()
        retrain_state = {"status": "succeeded", "result": result, "ended_at": datetime.utcnow().isoformat()}
        if model_service:
            model_service.load()
        _notify_retrain("succeeded", retrain_state)
    except Exception as exc:
        retrain_state = {"status": "failed", "error": str(exc), "ended_at": datetime.utcnow().isoformat()}
        _notify_retrain("failed", retrain_state)


@app.post("/admin/retrain")
async def trigger_retrain(background_tasks: BackgroundTasks, _: dict = Depends(admin_user)):
    if retrain_state.get("status") == "running":
        return JSONResponse({"status": "running"}, status_code=409)
    if rq_queue:
        job = rq_queue.enqueue(_background_retrain)
        retrain_state["status"] = "queued"
        retrain_state["job_id"] = job.id
        insert_audit_log(_.get("email"), "retrain_queued", {"job_id": job.id})
        return {"status": "queued", "job_id": job.id}
    background_tasks.add_task(_background_retrain)
    insert_audit_log(_.get("email"), "retrain_queued", {"job_id": None})
    return {"status": "queued"}


@app.get("/admin/retrain/status")
async def retrain_status(_: dict = Depends(admin_user)):
    return retrain_state


@app.get("/admin/retrain/versions")
async def retrain_versions(_: dict = Depends(admin_user)):
    return {"versions": list_versions()}


@app.post("/admin/retrain/rollback")
async def retrain_rollback(version: str, _: dict = Depends(admin_user)):
    ok = rollback(version)
    if not ok:
        raise HTTPException(status_code=404, detail="Version not found")
    if model_service:
        model_service.load()
    insert_audit_log(_.get("email"), "retrain_rollback", {"version": version})
    return {"status": "rolled_back", "version": version}


@app.get("/admin/metrics/trend", response_model=TrendResponse)
async def admin_trend(days: int = Query(30, ge=1, le=180), _: dict = Depends(admin_user)):
    points = prediction_trend(days=days)
    insert_audit_log(_.get("email"), "metrics_trend", {"days": days})
    return TrendResponse(points=[TrendPoint(**p) for p in points])


@app.get("/admin/activity", response_model=ActivityResponse)
async def admin_activity(limit: int = Query(50, ge=1, le=200), _: dict = Depends(admin_user)):
    items = recent_prediction_activity(limit=limit)
    insert_audit_log(_.get("email"), "activity_list", {"limit": limit})
    return ActivityResponse(items=[ActivityItem(**i) for i in items])