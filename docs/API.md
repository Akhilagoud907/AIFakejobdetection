# API Documentation

## Base URL
```
http://localhost:8000
```

For production, replace with your deployed domain.

## Authentication

### Public Endpoints
No authentication required:
- `/predict`
- `/health`
- `/model-info`
- `/feedback/flag`

### Admin Endpoints
Require Firebase ID token in `Authorization` header:
- All `/admin/*` endpoints

**Header Format**:
```
Authorization: Bearer <firebase-id-token>
```

**Getting an ID Token**:
```javascript
// Frontend (after Firebase login)
const idToken = await firebase.auth().currentUser.getIdToken();
```

---

## Public Endpoints

### 1. Health Check

Check if the API is running.

**Endpoint**: `GET /health`

**Authentication**: None

**Response**: `200 OK`
```json
{
  "status": "ok"
}
```

**Example**:
```powershell
Invoke-RestMethod -Method GET http://localhost:8000/health
```

---

### 2. Model Information

Get information about the active ML model.

**Endpoint**: `GET /model-info`

**Authentication**: None

**Response**: `200 OK`
```json
{
  "model_type": "Logistic Regression",
  "model_version": "2026-01-04_08-23-59",
  "feature_method": "TF-IDF",
  "metrics": {
    "accuracy": 0.9876,
    "precision": 0.9654,
    "recall": 0.9823,
    "f1_score": 0.9738
  },
  "training_date": "2026-01-04T08:23:59"
}
```

**Response Fields**:
- `model_type`: Model algorithm name
- `model_version`: Timestamp-based version identifier
- `feature_method`: Feature extraction technique
- `metrics`: Model performance metrics
- `training_date`: When the model was trained

**Example**:
```powershell
Invoke-RestMethod -Method GET http://localhost:8000/model-info
```

---

### 3. Predict Job Posting

Classify a job posting as fake or real.

**Endpoint**: `POST /predict`

**Authentication**: None

**Rate Limit**: 10 requests per minute per IP

**Request Body**:
```json
{
  "description": "string (required)",
  "company": "string (optional)",
  "location": "string (optional)",
  "salary": "string (optional)"
}
```

**Request Example**:
```json
{
  "description": "We are hiring a data analyst with 3+ years of experience in SQL, Python, and Tableau. Competitive salary and benefits.",
  "company": "Tech Corp",
  "location": "Remote",
  "salary": "$80,000 - $100,000"
}
```

**Response**: `200 OK`
```json
{
  "prediction": "real",
  "confidence": 87.43,
  "latency_ms": 45,
  "timestamp": "2026-01-04T10:15:30.123456",
  "warning": null
}
```

**Response Fields**:
- `prediction`: Classification result (`"fake"` or `"real"`)
- `confidence`: Confidence percentage (0-100)
- `latency_ms`: Processing time in milliseconds
- `timestamp`: ISO 8601 timestamp
- `warning`: Warning message if confidence < 60% (optional)

**Warning Example** (low confidence):
```json
{
  "prediction": "fake",
  "confidence": 52.3,
  "latency_ms": 43,
  "timestamp": "2026-01-04T10:15:30",
  "warning": "Low confidence prediction. Please verify manually."
}
```

**Error Responses**:

`400 Bad Request` - Missing or invalid input
```json
{
  "detail": "description field is required"
}
```

`429 Too Many Requests` - Rate limit exceeded
```json
{
  "detail": "Rate limit exceeded: 10 per 1 minute"
}
```

`500 Internal Server Error` - Model prediction failed
```json
{
  "detail": "Prediction failed"
}
```

**Example**:
```powershell
$body = @{
  description = "Earn $5000/month working from home! No experience required."
} | ConvertTo-Json

Invoke-RestMethod -Method POST -ContentType "application/json" -Body $body http://localhost:8000/predict
```

```bash
# cURL
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Senior Software Engineer position at a Fortune 500 company. 5+ years experience required.",
    "company": "Acme Corp",
    "location": "San Francisco, CA",
    "salary": "$120,000 - $150,000"
  }'
```

---

### 4. Flag Suspicious Job

Report a suspicious job posting for admin review.

**Endpoint**: `POST /feedback/flag`

**Authentication**: None

**Rate Limit**: 10 requests per minute per IP

**Request Body**:
```json
{
  "description": "string (required)",
  "company": "string (optional)",
  "location": "string (optional)",
  "salary": "string (optional)",
  "reason": "string (required)",
  "comments": "string (optional)"
}
```

**Reason Values**:
- `"too_good_to_be_true"`: Unrealistic promises
- `"suspicious_contact"`: Suspicious contact methods
- `"phishing"`: Appears to be phishing attempt
- `"other"`: Other reasons

**Request Example**:
```json
{
  "description": "Make $10,000 per week from home! No interview required. Just send your bank details.",
  "reason": "phishing",
  "comments": "Asks for bank account information upfront"
}
```

**Response**: `200 OK`
```json
{
  "message": "Thank you for flagging this post. Our team will review it.",
  "flag_id": 42
}
```

**Response Fields**:
- `message`: Confirmation message
- `flag_id`: Database ID of flagged post

**Error Responses**:

`400 Bad Request` - Missing required fields
```json
{
  "detail": "description and reason are required"
}
```

`429 Too Many Requests` - Rate limit exceeded
```json
{
  "detail": "Rate limit exceeded: 10 per 1 minute"
}
```

**Example**:
```powershell
$body = @{
  description = "Urgent! Transfer money for work visa processing."
  reason = "phishing"
  comments = "Requesting payment for visa"
} | ConvertTo-Json

Invoke-RestMethod -Method POST -ContentType "application/json" -Body $body http://localhost:8000/feedback/flag
```

---

## Admin Endpoints

All admin endpoints require Firebase authentication with `admin: true` custom claim.

### 5. Get Metrics Summary

Retrieve dashboard metrics.

**Endpoint**: `GET /admin/metrics/summary`

**Authentication**: Required (Admin)

**Query Parameters**: None

**Response**: `200 OK`
```json
{
  "total_predictions": 1523,
  "fake_count": 234,
  "real_count": 1289,
  "pending_flags": 12,
  "avg_confidence": 84.5,
  "avg_latency_ms": 42.3
}
```

**Response Fields**:
- `total_predictions`: Total number of predictions made
- `fake_count`: Number of fake predictions
- `real_count`: Number of real predictions
- `pending_flags`: Number of flagged posts pending review
- `avg_confidence`: Average confidence score (%)
- `avg_latency_ms`: Average prediction latency (milliseconds)

**Error Responses**:

`401 Unauthorized` - Missing or invalid token
```json
{
  "detail": "Not authenticated"
}
```

`403 Forbidden` - User is not admin
```json
{
  "detail": "Admin access required"
}
```

**Example**:
```powershell
$headers = @{
  Authorization = "Bearer $idToken"
}

Invoke-RestMethod -Method GET -Headers $headers http://localhost:8000/admin/metrics/summary
```

---

### 6. Get Prediction Trend

Get time-series prediction data for charts.

**Endpoint**: `GET /admin/metrics/trend`

**Authentication**: Required (Admin)

**Query Parameters**:
- `days` (optional): Number of days to fetch (default: 7, max: 90)

**Response**: `200 OK`
```json
{
  "labels": ["2026-01-01", "2026-01-02", "2026-01-03"],
  "total": [45, 67, 89],
  "fake": [8, 12, 15],
  "real": [37, 55, 74]
}
```

**Response Fields**:
- `labels`: Date labels (YYYY-MM-DD)
- `total`: Total predictions per day
- `fake`: Fake predictions per day
- `real`: Real predictions per day

**Example**:
```powershell
Invoke-RestMethod -Method GET -Headers $headers "http://localhost:8000/admin/metrics/trend?days=14"
```

---

### 7. Get Activity Log

Retrieve recent prediction events.

**Endpoint**: `GET /admin/metrics/activity`

**Authentication**: Required (Admin)

**Query Parameters**:
- `limit` (optional): Number of records to return (default: 50, max: 1000)

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": 1523,
      "prediction": 1,
      "confidence": 0.8743,
      "latency_ms": 45,
      "timestamp": "2026-01-04T10:15:30"
    }
  ]
}
```

**Response Fields**:
- `items`: Array of prediction events
  - `id`: Event ID
  - `prediction`: 1 (fake) or 0 (real)
  - `confidence`: Confidence score (0-1)
  - `latency_ms`: Processing time
  - `timestamp`: ISO 8601 timestamp

**Example**:
```powershell
Invoke-RestMethod -Method GET -Headers $headers "http://localhost:8000/admin/metrics/activity?limit=100"
```

---

### 8. Get Flagged Posts

Retrieve flagged posts for review.

**Endpoint**: `GET /admin/flags`

**Authentication**: Required (Admin)

**Query Parameters**:
- `status` (optional): Filter by status (`pending`, `validated`, `dismissed`)
- `limit` (optional): Number of records (default: 50, max: 500)

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": 42,
      "description": "Make $10,000 per week from home...",
      "prediction": 1,
      "reason": "phishing",
      "status": "pending",
      "confidence": 0.8234,
      "timestamp": "2026-01-04T09:30:15",
      "validated_label": null
    }
  ]
}
```

**Response Fields**:
- `items`: Array of flagged posts
  - `id`: Flag ID
  - `description`: Job description text
  - `prediction`: Model prediction (1=fake, 0=real)
  - `reason`: User-reported reason
  - `status`: Current status (`pending`, `validated`, `dismissed`)
  - `confidence`: Model confidence (0-1)
  - `timestamp`: When flagged
  - `validated_label`: Admin-assigned label (0 or 1, null if not validated)

**Example**:
```powershell
Invoke-RestMethod -Method GET -Headers $headers "http://localhost:8000/admin/flags?status=pending"
```

---

### 9. Update Flag Status

Mark a flagged post as validated or dismissed.

**Endpoint**: `POST /admin/flags/{flag_id}/status`

**Authentication**: Required (Admin)

**Path Parameters**:
- `flag_id`: ID of the flagged post

**Request Body**:
```json
{
  "status": "validated",
  "validated_label": 1
}
```

**Request Fields**:
- `status`: New status (`"validated"` or `"dismissed"`)
- `validated_label`: Ground truth label (0=real, 1=fake) - required if status is `validated`

**Response**: `200 OK`
```json
{
  "message": "Flag 42 updated to validated",
  "flag_id": 42
}
```

**Error Responses**:

`400 Bad Request` - Missing validated_label
```json
{
  "detail": "validated_label required when status is validated"
}
```

`404 Not Found` - Flag doesn't exist
```json
{
  "detail": "Flag not found"
}
```

**Example**:
```powershell
$body = @{
  status = "validated"
  validated_label = 1
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Headers $headers -ContentType "application/json" -Body $body http://localhost:8000/admin/flags/42/status
```

---

### 10. Export Predictions CSV

Export prediction events as CSV.

**Endpoint**: `GET /admin/export/predictions`

**Authentication**: Required (Admin)

**Query Parameters**:
- `start` (optional): Start datetime (ISO 8601)
- `end` (optional): End datetime (ISO 8601)

**Response**: `200 OK`
```csv
Content-Type: text/csv
Content-Disposition: attachment; filename=predictions_2026-01-04.csv

id,prediction,confidence,latency_ms,timestamp
1,1,0.8743,45,2026-01-04T10:15:30
2,0,0.9123,38,2026-01-04T10:16:45
```

**Example**:
```powershell
$start = "2026-01-01T00:00:00"
$end = "2026-01-04T23:59:59"

Invoke-RestMethod -Method GET -Headers $headers "http://localhost:8000/admin/export/predictions?start=$start&end=$end" -OutFile "predictions.csv"
```

---

### 11. Export Flags CSV

Export flagged posts as CSV.

**Endpoint**: `GET /admin/export/flags`

**Authentication**: Required (Admin)

**Query Parameters**:
- `start` (optional): Start datetime (ISO 8601)
- `end` (optional): End datetime (ISO 8601)

**Response**: `200 OK`
```csv
Content-Type: text/csv
Content-Disposition: attachment; filename=flags_2026-01-04.csv

id,prediction,reason,status,confidence,timestamp,validated_label
42,1,phishing,pending,0.8234,2026-01-04T09:30:15,
```

**Example**:
```powershell
Invoke-RestMethod -Method GET -Headers $headers http://localhost:8000/admin/export/flags -OutFile "flags.csv"
```

---

### 12. Generate PDF Report

Generate a PDF summary report.

**Endpoint**: `GET /admin/export/report`

**Authentication**: Required (Admin)

**Query Parameters**:
- `start` (optional): Start datetime (ISO 8601)
- `end` (optional): End datetime (ISO 8601)

**Response**: `200 OK`
```
Content-Type: application/pdf
Content-Disposition: attachment; filename=report_2026-01-04.pdf

<PDF binary data>
```

**Example**:
```powershell
Invoke-RestMethod -Method GET -Headers $headers http://localhost:8000/admin/export/report -OutFile "report.pdf"
```

---

### 13. Trigger Model Retraining

Start background model retraining.

**Endpoint**: `POST /admin/retrain`

**Authentication**: Required (Admin)

**Request Body**: None (empty)

**Response**: `200 OK`
```json
{
  "message": "Retraining started",
  "status": "running"
}
```

**Note**: Retraining runs in the background. Use `/admin/retrain/status` to check progress.

**Example**:
```powershell
Invoke-RestMethod -Method POST -Headers $headers http://localhost:8000/admin/retrain
```

---

### 14. Get Retrain Status

Check retraining progress.

**Endpoint**: `GET /admin/retrain/status`

**Authentication**: Required (Admin)

**Response**: `200 OK`
```json
{
  "status": "succeeded",
  "message": "Retraining completed successfully",
  "timestamp": "2026-01-04T11:30:45"
}
```

**Status Values**:
- `"idle"`: No retraining in progress
- `"running"`: Retraining in progress
- `"succeeded"`: Completed successfully
- `"failed"`: Failed with errors

**Example**:
```powershell
Invoke-RestMethod -Method GET -Headers $headers http://localhost:8000/admin/retrain/status
```

---

### 15. Get Model Versions

List all saved model versions.

**Endpoint**: `GET /admin/retrain/versions`

**Authentication**: Required (Admin)

**Response**: `200 OK`
```json
{
  "versions": [
    "2026-01-04_11-30-45",
    "2026-01-03_08-15-22",
    "2026-01-02_14-45-10"
  ],
  "current": "2026-01-04_11-30-45"
}
```

**Response Fields**:
- `versions`: Array of version identifiers (timestamps)
- `current`: Currently active version

**Example**:
```powershell
Invoke-RestMethod -Method GET -Headers $headers http://localhost:8000/admin/retrain/versions
```

---

### 16. Rollback Model

Rollback to a previous model version.

**Endpoint**: `POST /admin/retrain/rollback`

**Authentication**: Required (Admin)

**Query Parameters**:
- `version` (required): Version identifier to rollback to

**Response**: `200 OK`
```json
{
  "message": "Rolled back to version 2026-01-03_08-15-22",
  "version": "2026-01-03_08-15-22"
}
```

**Error Responses**:

`400 Bad Request` - Version not specified
```json
{
  "detail": "version parameter required"
}
```

`404 Not Found` - Version doesn't exist
```json
{
  "detail": "Version not found"
}
```

**Example**:
```powershell
Invoke-RestMethod -Method POST -Headers $headers "http://localhost:8000/admin/retrain/rollback?version=2026-01-03_08-15-22"
```

---

## Error Handling

### Standard Error Response
All errors follow this format:
```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes
- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

## Rate Limiting

### Limits
- **Public Endpoints** (`/predict`, `/feedback/flag`): 10 requests per minute per IP
- **Admin Endpoints**: No rate limit (authenticated users only)

### Rate Limit Headers
Response includes rate limit info:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1704369600
```

---

## CORS Configuration

### Allowed Origins
Default: `*` (all origins)

Production: Set `CORS_ALLOW_ORIGINS` environment variable
```
CORS_ALLOW_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com
```

### Allowed Methods
- GET, POST, PUT, DELETE, OPTIONS

### Allowed Headers
- Authorization, Content-Type

---

## Interactive API Documentation

FastAPI provides auto-generated interactive docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These allow testing endpoints directly from the browser.

---

**Document Version**: 1.0  
**Last Updated**: January 4, 2026  
**Maintainer**: Development Team
