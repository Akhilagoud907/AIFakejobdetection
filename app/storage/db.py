import os
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import create_engine, Column, Integer, Text, String, Float, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL, echo=False, future=True)
else:
    DB_PATH = os.getenv("DB_PATH", os.path.join("data", "app.db"))
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class FlaggedPost(Base):
    __tablename__ = "flagged_posts"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    reason = Column(String(100), nullable=False)
    comments = Column(Text, nullable=True)
    user_email = Column(String(200), nullable=True)
    prediction = Column(Integer, nullable=False)  # 0 real, 1 fake
    confidence = Column(String(50), nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    timestamp = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    admin_notes = Column(Text, nullable=True)
    validated_label = Column(Integer, nullable=True)  # ground truth set by admin: 0 real, 1 fake


class PredictionEvent(Base):
    __tablename__ = "prediction_events"
    id = Column(Integer, primary_key=True, index=True)
    prediction = Column(Integer, nullable=False)  # 0 real, 1 fake
    confidence = Column(Float, nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    source = Column(String(50), nullable=True)
    ip_hash = Column(String(128), nullable=True)
    timestamp = Column(String(50), nullable=False)
    model = Column(String(100), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(200), nullable=True)
    action = Column(String(100), nullable=False)
    detail = Column(Text, nullable=True)
    timestamp = Column(String(50), nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_flagged_columns()


def _get_existing_columns(table_name: str) -> List[str]:
    with engine.connect() as conn:
        res = conn.execute(text(f"PRAGMA table_info({table_name})"))
        return [row[1] for row in res.fetchall()]


def _ensure_flagged_columns():
    existing = _get_existing_columns("flagged_posts")
    alters = []
    if "status" not in existing:
        alters.append("ALTER TABLE flagged_posts ADD COLUMN status VARCHAR(50) DEFAULT 'pending'")
    if "admin_notes" not in existing:
        alters.append("ALTER TABLE flagged_posts ADD COLUMN admin_notes TEXT")
    if "validated_label" not in existing:
        alters.append("ALTER TABLE flagged_posts ADD COLUMN validated_label INTEGER")
    with engine.begin() as conn:
        for stmt in alters:
            conn.execute(text(stmt))
    _ensure_audit_table()


def _ensure_audit_table():
    existing_tables = _get_existing_tables()
    if "audit_logs" not in existing_tables:
        Base.metadata.tables["audit_logs"].create(bind=engine)


def _get_existing_tables():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        return [row[0] for row in res.fetchall()]


def get_db():
    return SessionLocal()


def insert_flag(record: Dict) -> int:
    db = get_db()
    try:
        item = FlaggedPost(
            description=record.get("description", ""),
            reason=record.get("reason", "other"),
            comments=record.get("comments"),
            user_email=record.get("user_email"),
            prediction=int(record.get("prediction", 0)),
            confidence=str(record.get("confidence", "")),
            processing_time_ms=int(record.get("processing_time_ms", 0)),
            timestamp=record.get("timestamp", datetime.utcnow().isoformat()),
            model=record.get("model", "unknown"),
            status=record.get("status", "pending"),
            admin_notes=record.get("admin_notes"),
            validated_label=record.get("validated_label"),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item.id
    finally:
        db.close()


def hash_ip(ip: Optional[str]) -> Optional[str]:
    if not ip:
        return None
    salt = os.getenv("IP_HASH_SALT", "")
    return hashlib.sha256(f"{ip}{salt}".encode("utf-8")).hexdigest()


def insert_prediction_event(record: Dict) -> int:
    db = get_db()
    try:
        item = PredictionEvent(
            prediction=int(record.get("prediction", 0)),
            confidence=float(record.get("confidence", 0.0)),
            processing_time_ms=int(record.get("processing_time_ms", 0)),
            source=record.get("source", "api"),
            ip_hash=record.get("ip_hash"),
            timestamp=record.get("timestamp", datetime.utcnow().isoformat()),
            model=record.get("model", "unknown"),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item.id
    finally:
        db.close()


def insert_audit_log(actor: Optional[str], action: str, detail: Optional[Dict] = None) -> None:
    db = get_db()
    try:
        entry = AuditLog(
            actor=actor,
            action=action,
            detail=json.dumps(detail or {}),
            timestamp=datetime.utcnow().isoformat(),
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


def list_flagged_posts(limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[Dict]:
    db = get_db()
    try:
        query = db.query(FlaggedPost).order_by(FlaggedPost.id.desc())
        if status:
            query = query.filter(FlaggedPost.status == status)
        items = query.offset(offset).limit(limit).all()
        results = []
        for item in items:
            results.append({
                "id": item.id,
                "description": item.description,
                "reason": item.reason,
                "comments": item.comments,
                "user_email": item.user_email,
                "prediction": item.prediction,
                "confidence": item.confidence,
                "processing_time_ms": item.processing_time_ms,
                "timestamp": item.timestamp,
                "model": item.model,
                "status": item.status,
                "admin_notes": item.admin_notes,
                "validated_label": item.validated_label,
            })
        return results
    finally:
        db.close()


def update_flag_status(flag_id: int, status_value: str, admin_notes: Optional[str] = None, validated_label: Optional[int] = None) -> bool:
    db = get_db()
    try:
        item = db.get(FlaggedPost, flag_id)
        if not item:
            return False
        item.status = status_value
        if admin_notes is not None:
            item.admin_notes = admin_notes
        if validated_label is not None:
            item.validated_label = int(validated_label)
        db.commit()
        return True
    finally:
        db.close()


def metrics_summary() -> Dict:
    db = get_db()
    try:
        totals = db.execute(text("SELECT COUNT(*), SUM(CASE WHEN prediction=1 THEN 1 ELSE 0 END) FROM prediction_events")).fetchone()
        flags = db.execute(text("SELECT COUNT(*), SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) FROM flagged_posts")).fetchone()
        total_pred = totals[0] or 0
        fake_pred = totals[1] or 0
        total_flags = flags[0] or 0
        pending_flags = flags[1] or 0
        return {
            "total_predictions": total_pred,
            "fake_predictions": fake_pred,
            "real_predictions": max(total_pred - fake_pred, 0),
            "total_flags": total_flags,
            "pending_flags": pending_flags,
        }
    finally:
        db.close()


def fetch_prediction_events(start_ts: Optional[str] = None, end_ts: Optional[str] = None):
    db = get_db()
    try:
        query = db.query(PredictionEvent)
        if start_ts:
            query = query.filter(PredictionEvent.timestamp >= start_ts)
        if end_ts:
            query = query.filter(PredictionEvent.timestamp <= end_ts)
        return query.order_by(PredictionEvent.id.desc()).all()
    finally:
        db.close()


def fetch_flagged_posts(start_ts: Optional[str] = None, end_ts: Optional[str] = None):
    db = get_db()
    try:
        query = db.query(FlaggedPost)
        if start_ts:
            query = query.filter(FlaggedPost.timestamp >= start_ts)
        if end_ts:
            query = query.filter(FlaggedPost.timestamp <= end_ts)
        return query.order_by(FlaggedPost.id.desc()).all()
    finally:
        db.close()


def prediction_trend(days: int = 30) -> List[Dict]:
    db = get_db()
    try:
        sql = text(
            """
            SELECT substr(timestamp, 1, 10) AS day,
                   COUNT(*) as total,
                   SUM(CASE WHEN prediction=1 THEN 1 ELSE 0 END) as fake
            FROM prediction_events
            WHERE timestamp >= date('now', :days)
            GROUP BY day
            ORDER BY day
            """
        )
        rows = db.execute(sql, {"days": f"-{days} day"}).fetchall()
        return [{"day": r[0], "total": r[1], "fake": r[2] or 0} for r in rows]
    finally:
        db.close()


def recent_prediction_activity(limit: int = 50) -> List[Dict]:
    db = get_db()
    try:
        items = db.query(PredictionEvent).order_by(PredictionEvent.id.desc()).limit(limit).all()
        return [
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
    finally:
        db.close()
