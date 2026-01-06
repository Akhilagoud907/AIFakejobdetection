# Database Schema Documentation

## Overview

The Fake Job Detector uses SQLAlchemy ORM with support for both SQLite (development) and PostgreSQL (production). The database stores prediction events, flagged posts, and audit logs.

## Database Configuration

### Connection Strings

**SQLite (Default)**:
```python
DATABASE_URL = "sqlite:///./data/app.db"
```

**PostgreSQL (Production)**:
```python
DATABASE_URL = "postgresql+psycopg2://user:password@host:5432/dbname"
```

Set via environment variable:
```powershell
$env:DATABASE_URL = "postgresql+psycopg2://user:pass@localhost:5432/fake_job_db"
```

---

## Tables

### 1. `flagged_posts`

Stores user-reported suspicious job postings for admin review.

#### Schema

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INTEGER | No | AUTO | Primary key |
| `description` | TEXT | No | - | Job description text |
| `company` | VARCHAR(200) | Yes | NULL | Company name (optional) |
| `location` | VARCHAR(200) | Yes | NULL | Job location (optional) |
| `salary` | VARCHAR(100) | Yes | NULL | Salary range (optional) |
| `prediction` | INTEGER | No | - | Model prediction (0=real, 1=fake) |
| `reason` | VARCHAR(100) | No | - | User-reported reason for flagging |
| `comments` | TEXT | Yes | NULL | Additional user comments |
| `status` | VARCHAR(20) | No | 'pending' | Review status |
| `confidence` | FLOAT | No | - | Model confidence score (0-1) |
| `timestamp` | DATETIME | No | CURRENT_TIMESTAMP | When flagged |
| `validated_label` | INTEGER | Yes | NULL | Admin-assigned ground truth (0 or 1) |

#### Constraints

- **Primary Key**: `id`
- **Check Constraints**:
  - `status IN ('pending', 'validated', 'dismissed')`
  - `prediction IN (0, 1)`
  - `validated_label IN (0, 1, NULL)`
  - `confidence >= 0 AND confidence <= 1`

#### Indexes

```sql
CREATE INDEX idx_flagged_status ON flagged_posts(status);
CREATE INDEX idx_flagged_timestamp ON flagged_posts(timestamp DESC);
```

#### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Awaiting admin review (default) |
| `validated` | Admin confirmed label, used in retraining |
| `dismissed` | Admin rejected flag, not used in retraining |

#### Example Rows

```sql
id | description                          | prediction | reason    | status    | confidence | validated_label
---|--------------------------------------|------------|-----------|-----------|------------|----------------
1  | Earn $5000/week from home...         | 1          | phishing  | validated | 0.85       | 1
2  | Senior Engineer at Fortune 500...    | 0          | other     | dismissed | 0.92       | NULL
3  | No experience required, high pay...  | 1          | too_good  | pending   | 0.78       | NULL
```

#### SQLAlchemy Model

```python
class FlaggedPost(Base):
    __tablename__ = "flagged_posts"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    company = Column(String(200))
    location = Column(String(200))
    salary = Column(String(100))
    prediction = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=False)
    comments = Column(Text)
    status = Column(String(20), nullable=False, default="pending")
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    validated_label = Column(Integer)
```

---

### 2. `prediction_events`

Logs all prediction requests for analytics and monitoring.

#### Schema

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INTEGER | No | AUTO | Primary key |
| `prediction` | INTEGER | No | - | Model prediction (0=real, 1=fake) |
| `confidence` | FLOAT | No | - | Model confidence score (0-1) |
| `latency_ms` | INTEGER | No | - | Prediction latency in milliseconds |
| `ip_hash` | VARCHAR(64) | Yes | NULL | Hashed IP address (privacy) |
| `timestamp` | DATETIME | No | CURRENT_TIMESTAMP | When prediction was made |

#### Constraints

- **Primary Key**: `id`
- **Check Constraints**:
  - `prediction IN (0, 1)`
  - `confidence >= 0 AND confidence <= 1`
  - `latency_ms >= 0`

#### Indexes

```sql
CREATE INDEX idx_prediction_timestamp ON prediction_events(timestamp DESC);
CREATE INDEX idx_prediction_class ON prediction_events(prediction);
```

#### Purpose

- **Analytics**: Track prediction distribution, confidence trends
- **Monitoring**: Track latency, volume over time
- **Privacy**: IP addresses are hashed with salt, not stored plaintext

#### Example Rows

```sql
id   | prediction | confidence | latency_ms | ip_hash                                                           | timestamp
-----|------------|------------|------------|-------------------------------------------------------------------|-------------------
1001 | 0          | 0.9234     | 42         | a3f5b2c1d4e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2 | 2026-01-04 10:15:30
1002 | 1          | 0.8567     | 38         | b4e6c3d2a5f9e0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3 | 2026-01-04 10:16:45
1003 | 0          | 0.9812     | 45         | c5f7d4e3b6a0f1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3g4 | 2026-01-04 10:18:12
```

#### SQLAlchemy Model

```python
class PredictionEvent(Base):
    __tablename__ = "prediction_events"
    id = Column(Integer, primary_key=True, index=True)
    prediction = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    ip_hash = Column(String(64))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
```

---

### 3. `audit_logs`

Records admin actions for compliance and security auditing.

#### Schema

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INTEGER | No | AUTO | Primary key |
| `action` | VARCHAR(100) | No | - | Action type (e.g., "export", "retrain") |
| `user_email` | VARCHAR(200) | No | - | Admin user email from Firebase |
| `details` | TEXT | Yes | NULL | JSON-encoded action details |
| `timestamp` | DATETIME | No | CURRENT_TIMESTAMP | When action occurred |

#### Constraints

- **Primary Key**: `id`

#### Indexes

```sql
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_user ON audit_logs(user_email);
CREATE INDEX idx_audit_action ON audit_logs(action);
```

#### Action Types

| Action | Description |
|--------|-------------|
| `export_predictions` | Admin exported predictions CSV |
| `export_flags` | Admin exported flags CSV |
| `export_report` | Admin generated PDF report |
| `metrics_view` | Admin viewed metrics summary |
| `retrain_start` | Admin triggered model retraining |
| `retrain_complete` | Model retraining completed |
| `retrain_failed` | Model retraining failed |
| `rollback` | Admin rolled back to previous model |
| `flag_updated` | Admin updated flag status |

#### Details Field (JSON)

Examples of JSON-encoded details:

**Export**:
```json
{
  "start": "2026-01-01T00:00:00",
  "end": "2026-01-04T23:59:59",
  "row_count": 1523
}
```

**Retrain**:
```json
{
  "duration_seconds": 45.3,
  "version": "2026-01-04_11-30-45",
  "metrics": {
    "accuracy": 0.9876,
    "precision": 0.9654,
    "recall": 0.9823,
    "f1_score": 0.9738
  }
}
```

**Rollback**:
```json
{
  "from_version": "2026-01-04_11-30-45",
  "to_version": "2026-01-03_08-15-22"
}
```

#### Example Rows

```sql
id | action              | user_email                | details                                                          | timestamp
---|---------------------|---------------------------|------------------------------------------------------------------|-------------------
1  | export_predictions  | admin@example.com         | {"start": "2026-01-01", "end": "2026-01-04", "row_count": 1523} | 2026-01-04 10:30:15
2  | retrain_start       | admin@example.com         | {}                                                               | 2026-01-04 11:00:00
3  | retrain_complete    | admin@example.com         | {"duration_seconds": 45.3, "version": "2026-01-04_11-30-45"}   | 2026-01-04 11:00:45
4  | flag_updated        | admin@example.com         | {"flag_id": 42, "new_status": "validated", "label": 1}          | 2026-01-04 11:15:22
```

#### SQLAlchemy Model

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    user_email = Column(String(200), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
```

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       flagged_posts                              │
├─────────────────────────────────────────────────────────────────┤
│ PK  id                INTEGER                                    │
│     description       TEXT                                       │
│     company           VARCHAR(200)   NULL                        │
│     location          VARCHAR(200)   NULL                        │
│     salary            VARCHAR(100)   NULL                        │
│     prediction        INTEGER        (0 or 1)                    │
│     reason            VARCHAR(100)                               │
│     comments          TEXT           NULL                        │
│     status            VARCHAR(20)    DEFAULT 'pending'           │
│     confidence        FLOAT                                      │
│     timestamp         DATETIME       DEFAULT CURRENT_TIMESTAMP   │
│     validated_label   INTEGER        NULL (0 or 1)               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     prediction_events                            │
├─────────────────────────────────────────────────────────────────┤
│ PK  id                INTEGER                                    │
│     prediction        INTEGER        (0 or 1)                    │
│     confidence        FLOAT                                      │
│     latency_ms        INTEGER                                    │
│     ip_hash           VARCHAR(64)    NULL                        │
│     timestamp         DATETIME       DEFAULT CURRENT_TIMESTAMP   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         audit_logs                               │
├─────────────────────────────────────────────────────────────────┤
│ PK  id                INTEGER                                    │
│     action            VARCHAR(100)                               │
│     user_email        VARCHAR(200)                               │
│     details           TEXT           NULL (JSON)                 │
│     timestamp         DATETIME       DEFAULT CURRENT_TIMESTAMP   │
└─────────────────────────────────────────────────────────────────┘
```

**Note**: Tables are independent with no foreign key relationships.

---

## Data Lifecycle

### flagged_posts
1. **Created**: When user flags a prediction via `/feedback/flag`
2. **Updated**: When admin changes status via `/admin/flags/{id}/status`
3. **Used**: Validated flags with `status='validated'` are used in model retraining
4. **Retention**: Indefinite (admin-managed)

### prediction_events
1. **Created**: After every `/predict` request
2. **Used**: For analytics, metrics, trend charts in admin dashboard
3. **Retention**: 90 days (configurable, can add cleanup job)

### audit_logs
1. **Created**: After admin actions (exports, retrain, flag updates)
2. **Used**: For compliance, security auditing, troubleshooting
3. **Retention**: 1 year minimum (compliance requirement)

---

## Database Initialization

### Automatic Table Creation

Tables are created automatically on first run via SQLAlchemy:

```python
from app.storage.db import Base, engine

# Creates all tables if they don't exist
Base.metadata.create_all(bind=engine)
```

### Manual Table Creation (SQL)

**SQLite**:
```sql
CREATE TABLE flagged_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    company VARCHAR(200),
    location VARCHAR(200),
    salary VARCHAR(100),
    prediction INTEGER NOT NULL CHECK(prediction IN (0, 1)),
    reason VARCHAR(100) NOT NULL,
    comments TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'validated', 'dismissed')),
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    validated_label INTEGER CHECK(validated_label IN (0, 1))
);

CREATE TABLE prediction_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction INTEGER NOT NULL CHECK(prediction IN (0, 1)),
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    latency_ms INTEGER NOT NULL CHECK(latency_ms >= 0),
    ip_hash VARCHAR(64),
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action VARCHAR(100) NOT NULL,
    user_email VARCHAR(200) NOT NULL,
    details TEXT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_flagged_status ON flagged_posts(status);
CREATE INDEX idx_flagged_timestamp ON flagged_posts(timestamp DESC);
CREATE INDEX idx_prediction_timestamp ON prediction_events(timestamp DESC);
CREATE INDEX idx_prediction_class ON prediction_events(prediction);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_user ON audit_logs(user_email);
CREATE INDEX idx_audit_action ON audit_logs(action);
```

**PostgreSQL**:
```sql
-- Similar to SQLite, but use SERIAL for AUTO INCREMENT
CREATE TABLE flagged_posts (
    id SERIAL PRIMARY KEY,
    -- ... rest same as above
);
```

---

## Query Patterns

### Common Queries

**Get pending flags**:
```sql
SELECT * FROM flagged_posts 
WHERE status = 'pending' 
ORDER BY timestamp DESC 
LIMIT 50;
```

**Get validated flags for retraining**:
```sql
SELECT description, validated_label 
FROM flagged_posts 
WHERE status = 'validated' AND validated_label IS NOT NULL;
```

**Get prediction metrics**:
```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as fake_count,
    SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END) as real_count,
    AVG(confidence) as avg_confidence,
    AVG(latency_ms) as avg_latency
FROM prediction_events;
```

**Get daily prediction trend**:
```sql
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total,
    SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as fake,
    SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END) as real
FROM prediction_events
WHERE timestamp >= DATE('now', '-7 days')
GROUP BY DATE(timestamp)
ORDER BY date;
```

**Get recent admin actions**:
```sql
SELECT action, user_email, details, timestamp
FROM audit_logs
ORDER BY timestamp DESC
LIMIT 20;
```

---

## Backup and Restore

### SQLite

**Backup**:
```powershell
# Copy database file
Copy-Item data/app.db data/app_backup_$(Get-Date -Format 'yyyy-MM-dd').db

# Or use SQLite command
sqlite3 data/app.db ".backup data/app_backup.db"
```

**Restore**:
```powershell
Copy-Item data/app_backup.db data/app.db
```

### PostgreSQL

**Backup**:
```bash
pg_dump -U username -h localhost -d fake_job_db > backup.sql

# Or with compression
pg_dump -U username -h localhost -d fake_job_db | gzip > backup.sql.gz
```

**Restore**:
```bash
psql -U username -h localhost -d fake_job_db < backup.sql

# Or from compressed
gunzip -c backup.sql.gz | psql -U username -h localhost -d fake_job_db
```

---

## Maintenance

### Data Cleanup

**Delete old prediction events (90 days)**:
```sql
DELETE FROM prediction_events 
WHERE timestamp < DATE('now', '-90 days');
```

**Delete old audit logs (1 year)**:
```sql
DELETE FROM audit_logs 
WHERE timestamp < DATE('now', '-365 days');
```

### Optimization

**Analyze tables (SQLite)**:
```sql
ANALYZE flagged_posts;
ANALYZE prediction_events;
ANALYZE audit_logs;
```

**Vacuum (SQLite)**:
```sql
VACUUM;
```

**PostgreSQL maintenance**:
```sql
VACUUM ANALYZE flagged_posts;
VACUUM ANALYZE prediction_events;
VACUUM ANALYZE audit_logs;
```

---

## Migration Guide

### SQLite to PostgreSQL

1. **Export data**:
```bash
sqlite3 data/app.db .dump > dump.sql
```

2. **Clean up SQL (remove SQLite-specific syntax)**:
```bash
sed -i 's/AUTOINCREMENT//' dump.sql
sed -i 's/INTEGER PRIMARY KEY/SERIAL PRIMARY KEY/' dump.sql
```

3. **Import to PostgreSQL**:
```bash
psql -U username -h localhost -d fake_job_db < dump.sql
```

4. **Update DATABASE_URL** environment variable

---

## Security Considerations

### IP Address Hashing
- IP addresses in `prediction_events` are hashed with SHA-256 and salt
- Salt stored in `IP_HASH_SALT` environment variable
- Cannot reverse hash to get original IP (privacy protection)

### Sensitive Data
- Job descriptions may contain PII (not validated/sanitized)
- Admin emails stored in audit logs (authenticated users)
- No passwords stored (Firebase handles authentication)

### Access Control
- Database access restricted to application only
- No direct public database access
- Admin endpoints require Firebase authentication

---

**Document Version**: 1.0  
**Last Updated**: January 4, 2026  
**Maintainer**: Development Team
