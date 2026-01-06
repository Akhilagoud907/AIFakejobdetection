# System Architecture Documentation

## Overview

The Fake Job Detector is a web-based machine learning system that analyzes job postings to detect fraudulent listings. The system follows a three-tier architecture with a FastAPI backend, client-side frontend, and SQLite/PostgreSQL database.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │   Public Interface   │    │   Admin Dashboard    │      │
│  │   (index.html)       │    │   (admin.html)       │      │
│  │                      │    │                      │      │
│  │  - Job submission    │    │  - Metrics view      │      │
│  │  - Prediction view   │    │  - Flag management   │      │
│  │  - Flag reporting    │    │  - Model retraining  │      │
│  │                      │    │  - Data exports      │      │
│  └──────────────────────┘    └──────────────────────┘      │
│           │                            │                     │
│           │                            │                     │
│           └────────────┬───────────────┘                     │
│                        │                                     │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         │ HTTP/HTTPS
                         │
┌────────────────────────┼─────────────────────────────────────┐
│                        │     APPLICATION LAYER                │
├────────────────────────┼─────────────────────────────────────┤
│                        ▼                                      │
│           ┌─────────────────────────┐                        │
│           │   FastAPI Application   │                        │
│           │      (app/main.py)      │                        │
│           └─────────────────────────┘                        │
│                        │                                      │
│          ┌─────────────┼─────────────┐                       │
│          │             │             │                       │
│          ▼             ▼             ▼                       │
│  ┌──────────────┐ ┌──────────┐ ┌──────────────┐           │
│  │   Public     │ │  Admin   │ │ Static File  │           │
│  │   Routes     │ │  Routes  │ │   Serving    │           │
│  │              │ │          │ │              │           │
│  │ /predict     │ │ /admin/* │ │ /static/*    │           │
│  │ /health      │ │          │ │              │           │
│  │ /model-info  │ │ Auth:    │ │              │           │
│  │ /feedback/*  │ │ Firebase │ │              │           │
│  └──────────────┘ └──────────┘ └──────────────┘           │
│          │             │                                     │
│          └─────────────┼─────────────┐                      │
│                        │             │                      │
│                        ▼             ▼                      │
│              ┌──────────────┐  ┌──────────────┐           │
│              │   Services   │  │     Auth     │           │
│              │              │  │              │           │
│              │ - Inference  │  │ - Firebase   │           │
│              │ - Retrain    │  │   Admin SDK  │           │
│              │ - Notify     │  │ - Token      │           │
│              │              │  │   Validation │           │
│              └──────────────┘  └──────────────┘           │
│                        │                                     │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         │
┌────────────────────────┼─────────────────────────────────────┐
│                        │      DATA LAYER                      │
├────────────────────────┼─────────────────────────────────────┤
│                        ▼                                      │
│           ┌─────────────────────────┐                        │
│           │  Database (SQLAlchemy)  │                        │
│           │   SQLite/PostgreSQL     │                        │
│           └─────────────────────────┘                        │
│                        │                                      │
│           ┌────────────┴────────────┐                        │
│           │                         │                        │
│           ▼                         ▼                        │
│  ┌─────────────────┐      ┌─────────────────┐              │
│  │  Tables:        │      │  ML Artifacts:  │              │
│  │                 │      │                 │              │
│  │ - flagged_posts │      │ - TF-IDF        │              │
│  │ - predictions   │      │ - LogReg Model  │              │
│  │ - audit_logs    │      │ - BiLSTM Model  │              │
│  │                 │      │ - Tokenizer     │              │
│  └─────────────────┘      └─────────────────┘              │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Client Layer

#### Public Interface (`app/frontend/index.html`)
- **Purpose**: Allows users to submit job descriptions for fraud detection
- **Features**:
  - Job description text input
  - Optional metadata (company, location, salary)
  - Real-time prediction results
  - Flag suspicious predictions
  - Example job loader
- **Technology**: HTML5, CSS3, Vanilla JavaScript
- **API Communication**: RESTful HTTP via Fetch API

#### Admin Dashboard (`app/frontend/admin.html`)
- **Purpose**: Administrative interface for system monitoring and management
- **Features**:
  - Authentication via Firebase
  - Real-time metrics and charts
  - Flagged posts management
  - Model retraining controls
  - Data export (CSV, PDF)
  - Activity logs
- **Technology**: HTML5, CSS3, JavaScript, Chart.js
- **Authentication**: Firebase Authentication with custom claims

### 2. Application Layer

#### FastAPI Backend (`app/main.py`)
- **Framework**: FastAPI 0.115.0
- **Python Version**: 3.10+
- **Key Features**:
  - RESTful API endpoints
  - CORS middleware for cross-origin requests
  - Rate limiting (SlowAPI)
  - Firebase authentication middleware
  - Error handling (404, 500)
  - Static file serving
  - Background task support

#### Core Modules

##### Inference Service (`app/models/inference.py`)
- **Purpose**: ML model loading and prediction
- **Models Supported**:
  - Logistic Regression (primary)
  - BiLSTM (optional)
- **Features**:
  - TF-IDF vectorization
  - Model caching
  - Confidence scoring
  - Latency tracking

##### Retraining Service (`app/services/retrain.py`)
- **Purpose**: Automated model retraining pipeline
- **Features**:
  - Data aggregation (base + validated flags)
  - Model versioning
  - Metrics tracking
  - Rollback support
  - Background execution

##### Authentication (`app/auth/firebase.py`)
- **Purpose**: Firebase Admin SDK integration
- **Features**:
  - ID token verification
  - Custom claims validation
  - Admin user management

##### Database Layer (`app/storage/db.py`)
- **ORM**: SQLAlchemy 2.0
- **Models**:
  - `FlaggedPost`: User-reported suspicious jobs
  - `PredictionEvent`: All prediction logs
  - `AuditLog`: Admin action tracking

##### Notification Service (`app/services/notify.py`)
- **Purpose**: Email notifications
- **Features**:
  - SMTP integration
  - Retrain completion alerts
  - Export delivery

### 3. Data Layer

#### Database Schema
- **Primary**: SQLite (development)
- **Production**: PostgreSQL recommended
- **Tables**:
  - `flagged_posts`: ID, description, prediction, reason, status, confidence, timestamp
  - `prediction_events`: ID, prediction, confidence, latency, IP hash, timestamp
  - `audit_logs`: ID, action, user, details, timestamp

#### ML Artifacts
- **Location**: `m1_outputs/`, `m2_outputs/`, `m2_versions/`
- **Files**:
  - `tfidf_vectorizer.pkl`: TF-IDF feature extractor
  - `logreg_best.joblib`: Trained logistic regression model
  - `logreg_metrics.json`: Model performance metrics
  - `bilstm_model.keras`: Optional LSTM model
  - `tokenizer.pkl`: Text tokenizer for LSTM

## Data Flow

### Prediction Flow
```
1. User submits job description
   ↓
2. Frontend sends POST /predict
   ↓
3. Rate limiter checks request
   ↓
4. Text preprocessing (lowercase, clean)
   ↓
5. TF-IDF vectorization
   ↓
6. Model inference (LogReg/BiLSTM)
   ↓
7. Confidence calculation
   ↓
8. Log prediction event to DB
   ↓
9. Return result (classification, confidence, latency)
   ↓
10. Frontend displays result with visual indicators
```

### Flag Flow
```
1. User flags suspicious prediction
   ↓
2. Frontend sends POST /feedback/flag
   ↓
3. Validate payload
   ↓
4. Save to flagged_posts table (status: pending)
   ↓
5. Return success
   ↓
6. Admin reviews in dashboard
   ↓
7. Admin marks as validated/dismissed
   ↓
8. Validated flags used in retraining
```

### Retraining Flow
```
1. Admin clicks "Retrain Model"
   ↓
2. POST /admin/retrain (background task)
   ↓
3. Load base dataset (fake_job_postings.csv)
   ↓
4. Query validated flags (status=validated)
   ↓
5. Merge datasets
   ↓
6. Train/test split
   ↓
7. TF-IDF vectorization
   ↓
8. Train LogReg with GridSearchCV
   ↓
9. Evaluate metrics (accuracy, precision, recall, F1)
   ↓
10. Save versioned artifacts (m2_versions/)
   ↓
11. Copy to active location (m2_outputs/)
   ↓
12. Log audit entry
   ↓
13. Send notification email (if configured)
   ↓
14. Return status to admin dashboard
```

## Security Architecture

### Authentication & Authorization
- **Public Endpoints**: No authentication required
  - `/predict`, `/health`, `/model-info`, `/feedback/flag`
- **Admin Endpoints**: Firebase ID token required
  - All `/admin/*` routes
  - Token validated via Firebase Admin SDK
  - Custom claim `admin: true` required

### Security Measures
1. **Rate Limiting**: 10 requests/minute per IP on predict/flag
2. **CORS**: Configurable allowed origins
3. **Input Validation**: Pydantic models for all payloads
4. **IP Hashing**: Prediction logs hash IPs with salt
5. **Firebase Auth**: Industry-standard authentication
6. **Secret Management**: Environment variables for credentials
7. **HTTPS**: TLS termination at proxy/load balancer

## Technology Stack

### Backend
- **Framework**: FastAPI 0.115.0
- **Language**: Python 3.10+
- **Web Server**: Uvicorn (ASGI)
- **ORM**: SQLAlchemy 2.0.22
- **Authentication**: Firebase Admin SDK 6.5.0
- **Rate Limiting**: SlowAPI
- **ML Libraries**: scikit-learn 1.3.2, TensorFlow 2.15+ (optional)

### Frontend
- **Languages**: HTML5, CSS3, JavaScript (ES6+)
- **Libraries**: 
  - Chart.js 4.4.1 (visualization)
  - Firebase SDK 9.x (authentication)
- **Build**: None (vanilla JS)

### Database
- **Development**: SQLite 3
- **Production**: PostgreSQL 13+
- **Driver**: psycopg2 (PostgreSQL)

### Deployment
- **Containerization**: Docker
- **Process Manager**: Uvicorn/Gunicorn
- **Reverse Proxy**: Nginx/Apache (recommended)
- **Cloud Platforms**: AWS, GCP, Azure, Heroku

## Scalability Considerations

### Current Limitations
- In-memory model loading (single instance)
- SQLite (development) - file-based, single writer
- Synchronous prediction inference
- Background retraining blocks main thread

### Scaling Strategies

#### Horizontal Scaling
1. **Load Balancer**: Distribute traffic across multiple instances
2. **Shared Database**: PostgreSQL with connection pooling
3. **Shared Storage**: S3/GCS for ML artifacts
4. **Redis Session Store**: Distributed caching

#### Performance Optimization
1. **Model Caching**: Pre-load models at startup
2. **Connection Pooling**: Database connection reuse
3. **Async Workers**: Celery/RQ for background jobs
4. **CDN**: Static file serving via CDN
5. **Caching**: Redis for frequent queries

#### High Availability
1. **Database Replication**: Primary-replica setup
2. **Health Checks**: Kubernetes liveness/readiness probes
3. **Monitoring**: Prometheus + Grafana
4. **Alerting**: Error rate/latency thresholds
5. **Backup**: Automated daily backups

## Monitoring & Observability

### Logging
- **Application Logs**: Python logging module
- **Access Logs**: Uvicorn access logs
- **Error Logs**: Exception stack traces
- **Audit Logs**: Database table for admin actions

### Metrics
- **Prediction Count**: Total predictions
- **Fake/Real Distribution**: Classification breakdown
- **Average Latency**: Response time tracking
- **Error Rate**: 4xx/5xx responses
- **Active Flags**: Pending user reports

### Alerting
- **High Error Rate**: >5% 5xx responses
- **High Latency**: >1s average response time
- **Model Failure**: Inference errors
- **Database Issues**: Connection failures

## Disaster Recovery

### Backup Strategy
- **Database**: Daily automated backups
- **ML Artifacts**: Version-controlled storage
- **Configuration**: Environment variables in secret store
- **Recovery Time Objective (RTO)**: 1 hour
- **Recovery Point Objective (RPO)**: 24 hours

### Rollback Procedures
1. **Model Rollback**: Admin UI version selector
2. **Code Rollback**: Git revert + redeploy
3. **Database Rollback**: Restore from backup
4. **Configuration Rollback**: Environment variable update

## Compliance & Privacy

### Data Retention
- **Prediction Events**: 90 days (configurable)
- **Flagged Posts**: Indefinite (admin managed)
- **Audit Logs**: 1 year minimum

### PII Handling
- **IP Addresses**: Hashed with salt
- **Job Descriptions**: May contain PII (not validated)
- **User Emails**: Firebase authentication only

### GDPR Considerations
- **Right to Erasure**: Manual admin deletion
- **Data Portability**: CSV export functionality
- **Consent**: Implicit via usage
- **Privacy Policy**: Recommended but not included

## Future Enhancements

### Planned Features
1. **Real-time Notifications**: WebSocket for live updates
2. **Advanced Analytics**: ML explainability (LIME/SHAP)
3. **Multi-model Ensemble**: Voting classifier
4. **API Rate Plans**: Tiered usage limits
5. **User Accounts**: Prediction history tracking
6. **Scheduled Retraining**: Automated weekly retraining
7. **A/B Testing**: Model comparison framework
8. **Mobile App**: Native iOS/Android clients

### Architecture Evolution
1. **Microservices**: Separate inference/admin services
2. **Event-Driven**: Kafka/RabbitMQ message queue
3. **Serverless**: AWS Lambda/Google Cloud Functions
4. **MLOps Pipeline**: Automated training/deployment (MLflow/Kubeflow)

---

**Document Version**: 1.0  
**Last Updated**: January 4, 2026  
**Maintainer**: Development Team
