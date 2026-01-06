# Fake Job Detector — Milestone 4 (Admin & Ops)

This milestone keeps the public predictor UI and adds an admin dashboard with Firebase-authenticated access, metrics, exports, and a retrain trigger.

## Features
- FastAPI backend with `/predict`, `/health`, `/model-info`, `/feedback/flag`
- Admin-only endpoints (Firebase ID token required): `/admin/metrics/summary`, `/admin/flags`, `/admin/flags/{id}/status`, `/admin/export/*`, `/admin/retrain`
- Retrain pipeline with model versioning and rollback; retrain uses validated flagged posts plus base dataset; status/versions endpoints for admin UI
- Admin exports: CSV for predictions/flags (with optional start/end), PDF summary report; trend/activity metrics for dashboard
- Audit logging: admin actions (exports, metrics, retrain, flags) recorded in `audit_logs` table
- Loads saved model artifacts from `m1_outputs` / `m2_outputs`; fallback training if missing
- SQLite storage for flagged posts, plus prediction event logging
- Public frontend (`app/frontend/index.html`) and admin dashboard (`app/frontend/admin.html`)
- Rate limiting on predict/flag endpoints

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
. ".venv\Scripts\Activate.ps1"
pip install --upgrade pip
pip install -r requirements.txt
```

### Firebase (admin auth)
- Create a Firebase project and service account key; download JSON and set `FIREBASE_CREDENTIALS` to its path.
- Optionally set `FIREBASE_PROJECT_ID`.
- In Firebase Auth, create an admin user and assign a custom claim `admin: true`.

Optional (if using BiLSTM artifacts):
```powershell
pip install tensorflow
```

## Run Backend
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs

## Open Frontend
- Public: open `app/frontend/index.html` in your browser (or serve statically). Update `API_BASE` in `app/static/js/app.js` if needed.
- Admin: open `app/frontend/admin.html`. Login with Firebase email/password; the page will call admin endpoints using the ID token.

## Retraining & Versions
- Admin UI retrain button triggers background retrain using `fake_job_postings.csv` + flagged posts that were marked as Real/Fake.
- Versions are saved under `m2_versions/`; latest is copied to `m2_outputs/logreg_best.joblib` and metrics to `m2_outputs/logreg_metrics.json`.
- Rollback via admin UI (select version) or API `/admin/retrain/rollback?version=...`.

## Environment
- `FIREBASE_CREDENTIALS`: path to Firebase service account JSON (required for admin auth)
- `FIREBASE_PROJECT_ID`: optional; used during Firebase Admin init
- `DATA_PATH`: override default dataset path for retraining (default `fake_job_postings.csv`)
- `IP_HASH_SALT`: optional salt for IP hashing in prediction logs
- `DATABASE_URL`: optional; e.g., `postgresql+psycopg2://user:pass@host:5432/dbname` (defaults to SQLite file `data/app.db`)
- `CORS_ALLOW_ORIGINS`: comma-separated list of allowed origins (default `*`)
- `USE_RQ`: set to `1` to use Redis/RQ for retrain jobs; requires `REDIS_URL`
- `REDIS_URL`: Redis connection string (e.g., `redis://localhost:6379/0`)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, `SMTP_TO`: optional SMTP config for notifications and emailed exports

## Production readiness notes
- Rate limiting: Predict/flag endpoints limited via SlowAPI; adjust defaults in `app/main.py`.
- Error pages: Friendly 404/500 handlers added in `app/main.py`; keep stack traces out of responses.
- Logging: Basic app logger enabled; configure `uvicorn`/`gunicorn` access/error logs; avoid logging PII. Add alerting on 5xx spikes.
- HTTPS: Terminate TLS at the proxy/load balancer; set CORS to allowed origins for production.
- Secrets: Keep Firebase service account JSON and salts in environment/secret store, not in repo.
- Database: SQLite by default; set `DATABASE_URL` (Postgres recommended for multi-user/scale) with the same ORM models.
- Background jobs: Retrain runs inline background task; for heavier loads, offload to a worker/queue (e.g., RQ/Celery) and persist job state.
- Performance: Ensure `m1_outputs/m2_outputs` are present to avoid fallback training at startup; warm up model on deploy.
- Notifications/exports: If SMTP is set, retrain completion/failure emails and `/admin/export/email` attachments are enabled. Use cron/worker to call the endpoint for scheduled exports.

## Artifacts
Expected files from previous milestones:
- `m1_outputs/tfidf_vectorizer.pkl`
- `m2_outputs/logreg_best.joblib`, `m2_outputs/logreg_metrics.json`
- Optional: `m2_outputs/bilstm_model.keras`, `m2_outputs/tokenizer.pkl`, `m2_outputs/bilstm_metrics.json`

If artifacts are missing but `fake_job_postings.csv` exists, the backend will train a quick fallback Logistic Regression at startup.

## Test Endpoints
```powershell
# Health
Invoke-RestMethod -Method GET http://localhost:8000/health

# Model info
Invoke-RestMethod -Method GET http://localhost:8000/model-info

# Predict
$body = @{ description = "We are hiring a data analyst with strong SQL and dashboarding skills." } | ConvertTo-Json
Invoke-RestMethod -Method POST -ContentType application/json -Body $body http://localhost:8000/predict

# Flag
$flag = @{ description = "Suspicious job post"; reason = "phishing"; comments = "Email asks for credentials" } | ConvertTo-Json
Invoke-RestMethod -Method POST -ContentType application/json -Body $flag http://localhost:8000/feedback/flag
```

## Docker (optional)
```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY m1_outputs ./m1_outputs
COPY m2_outputs ./m2_outputs
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Build and run:
```powershell
docker build -t fake-job-detector .
docker run -p 8000:8000 fake-job-detector
```

## Notes
- Response includes classification, confidence (0-100%), processing time, and timestamp.
- Low-confidence results (< 60%) show a warning in the UI.
- Flagged posts are saved to `data/app.db` (SQLite).