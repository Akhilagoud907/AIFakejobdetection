# Troubleshooting Guide

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Can't access website | Check if server is running |
| Slow predictions | Check network/server load |
| Login fails | Verify credentials and admin claims |
| Retrain fails | Check validated flags exist |
| Export fails | Verify date format and backend status |
| Charts not showing | Hard refresh (Ctrl+Shift+R) |

---

## Table of Contents

1. [Installation & Setup Issues](#installation--setup-issues)
2. [Backend/Server Issues](#backendserver-issues)
3. [Frontend/UI Issues](#frontendui-issues)
4. [Authentication Issues](#authentication-issues)
5. [Prediction Issues](#prediction-issues)
6. [Admin Dashboard Issues](#admin-dashboard-issues)
7. [Model Management Issues](#model-management-issues)
8. [Database Issues](#database-issues)
9. [Performance Issues](#performance-issues)
10. [Network & API Issues](#network--api-issues)

---

## Installation & Setup Issues

### Python Dependencies Installation Fails

**Symptoms**:
- `pip install -r requirements.txt` fails
- Module import errors
- Version conflicts

**Solutions**:

1. **Update pip**:
```powershell
python -m pip install --upgrade pip
```

2. **Use compatible Python version**:
```powershell
python --version  # Should be 3.10 or higher
```

3. **Clean install**:
```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Install problematic packages individually**:
```powershell
pip install fastapi==0.115.0
pip install sqlalchemy==2.0.22
pip install scikit-learn==1.3.2
```

### Firebase Configuration Not Found

**Error**: `FIREBASE_CREDENTIALS environment variable not set`

**Solutions**:

1. **Download service account key** from Firebase Console:
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Save JSON file securely

2. **Set environment variable**:
```powershell
$env:FIREBASE_CREDENTIALS = "C:\path\to\firebase-key.json"
```

3. **Verify file path**:
```powershell
Test-Path $env:FIREBASE_CREDENTIALS  # Should return True
```

4. **Make permanent** (optional):
```powershell
[System.Environment]::SetEnvironmentVariable('FIREBASE_CREDENTIALS', 'C:\path\to\firebase-key.json', 'User')
```

### Missing ML Artifacts

**Error**: `TF-IDF vectorizer not found` or `Model file not found`

**Solutions**:

1. **Check artifact files exist**:
```powershell
ls m1_outputs/  # Should show tfidf_vectorizer.pkl
ls m2_outputs/  # Should show logreg_best.joblib
```

2. **Run artifact generation script** (if available):
```powershell
python scripts/generate_artifacts.py
```

3. **Let system train fallback model**:
   - Ensure `fake_job_postings.csv` exists in project root
   - Start server - it will train a basic model automatically

4. **Copy from backup** (if available):
```powershell
Copy-Item backup/m1_outputs/* m1_outputs/
Copy-Item backup/m2_outputs/* m2_outputs/
```

### Database Initialization Fails

**Error**: `Cannot create database` or `Permission denied`

**Solutions**:

1. **Create data directory**:
```powershell
New-Item -ItemType Directory -Path data -Force
```

2. **Check write permissions**:
```powershell
# Should allow writing
Test-Path -PathType Container -Path data
```

3. **Manual database creation**:
```powershell
# For SQLite
sqlite3 data/app.db ".databases"  # Creates empty database
```

4. **Use alternative database URL**:
```powershell
$env:DATABASE_URL = "sqlite:///./app.db"  # Creates in project root
```

---

## Backend/Server Issues

### Server Won't Start

**Symptoms**:
- `uvicorn` command fails
- Port already in use
- Import errors

**Diagnostic Commands**:
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Test Python imports
python -c "from app.main import app; print('OK')"

# Check virtual environment is active
where python  # Should point to .venv
```

**Solutions**:

1. **Kill process on port 8000**:
```powershell
# Find process ID
$pid = (Get-NetTCPConnection -LocalPort 8000).OwningProcess
# Kill process
Stop-Process -Id $pid -Force
```

2. **Use different port**:
```powershell
uvicorn app.main:app --port 8001
```

3. **Check import errors**:
```powershell
python -m app.main  # Shows detailed error
```

4. **Verify environment variables**:
```powershell
$env:FIREBASE_CREDENTIALS  # Should show path
$env:DATABASE_URL  # Check if set
```

### Server Crashes During Runtime

**Symptoms**:
- Server stops responding
- Uvicorn exits unexpectedly
- Memory errors

**Solutions**:

1. **Check logs** for error messages:
```powershell
# Run without reload to see full traceback
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

2. **Monitor resource usage**:
```powershell
# Check memory usage
Get-Process python | Select-Object ProcessName,WS
```

3. **Increase memory** (if needed):
   - Close other applications
   - Increase virtual memory
   - Consider cloud deployment

4. **Disable problematic features**:
   - Comment out background tasks
   - Disable model auto-loading
   - Reduce worker count

### Slow Server Response

**Symptoms**:
- Predictions take >1 second
- Dashboard loads slowly
- Timeouts

**Diagnostic**:
```powershell
# Test API response time
Measure-Command { Invoke-RestMethod http://localhost:8000/health }
```

**Solutions**:

1. **Check database size**:
```powershell
ls data/app.db  # If >100MB, consider cleanup
```

2. **Clean old data**:
```powershell
# Connect to database
sqlite3 data/app.db

# Delete old predictions
DELETE FROM prediction_events WHERE timestamp < DATE('now', '-90 days');

# Vacuum database
VACUUM;
```

3. **Optimize database**:
```sql
-- In sqlite3
ANALYZE;
```

4. **Restart server**:
```powershell
Stop-Process -Name python -Force
# Start server again
```

---

## Frontend/UI Issues

### Page Not Loading

**Symptoms**:
- Blank page
- 404 Not Found
- Connection refused

**Solutions**:

1. **Verify server is running**:
```powershell
Invoke-RestMethod http://localhost:8000/health
```

2. **Check correct URL**:
   - Public interface: `http://localhost:8000/` or `http://localhost:8000/static/index.html`
   - Admin dashboard: `http://localhost:8000/admin`

3. **Clear browser cache**:
   - Press `Ctrl+Shift+Delete`
   - Select "Cached images and files"
   - Click "Clear data"

4. **Try different browser**:
   - Test in Chrome, Firefox, or Edge
   - Check browser console for errors (F12)

### JavaScript Errors

**Symptoms**:
- Buttons don't work
- Forms don't submit
- Console shows errors

**Diagnostic**:
1. Press `F12` to open Developer Tools
2. Go to Console tab
3. Look for red error messages

**Common Errors & Fixes**:

**Error**: `Firebase is not defined`
**Fix**: Check internet connection - Firebase SDK loads from CDN

**Error**: `Cannot read property of undefined`
**Fix**: Hard refresh page (Ctrl+Shift+R)

**Error**: `NetworkError when attempting to fetch resource`
**Fix**: Check backend server is running

**Error**: `Unexpected token <`
**Fix**: API returned HTML instead of JSON - check backend endpoint

### Styles Not Applying

**Symptoms**:
- Page looks broken
- No colors/formatting
- Layout is wrong

**Solutions**:

1. **Hard refresh**:
```
Ctrl+Shift+R  or  Ctrl+F5
```

2. **Check CSS file loads**:
   - F12 > Network tab
   - Refresh page
   - Look for `styles.css` - should be 200 OK

3. **Verify file paths**:
   - Open browser console (F12)
   - Look for 404 errors for CSS files

4. **Check file location**:
```powershell
Test-Path app/static/css/styles.css  # Should be True
```

### Forms Not Submitting

**Symptoms**:
- Submit button does nothing
- No error messages
- Form stays on same page

**Solutions**:

1. **Check browser console** (F12) for JavaScript errors

2. **Verify network requests**:
   - F12 > Network tab
   - Submit form
   - Look for POST request to `/predict` or `/feedback/flag`
   - Check response status code

3. **Test API directly**:
```powershell
$body = @{ description = "Test job" } | ConvertTo-Json
Invoke-RestMethod -Method POST -ContentType "application/json" -Body $body http://localhost:8000/predict
```

4. **Check rate limiting**:
   - Wait 60 seconds
   - Try again

---

## Authentication Issues

### Cannot Log In to Admin Dashboard

**Error Messages & Solutions**:

#### "No account found with this email. Please sign up for a new account."

**Cause**: Email not registered in Firebase

**Solutions**:
1. Click "Sign Up" link
2. Create account with email/password
3. Contact admin to set admin claim:

```powershell
# Admin runs this command
python -c "
import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate('path/to/firebase-key.json')
firebase_admin.initialize_app(cred)
user = auth.get_user_by_email('your-email@example.com')
auth.set_custom_user_claims(user.uid, {'admin': True})
print('Admin claim set')
"
```

#### "Incorrect password. Please try again."

**Causes & Solutions**:
- **Wrong password**: Use password reset
- **Caps Lock on**: Check keyboard
- **Browser autofill wrong**: Clear and retype

**Reset password**:
1. Go to Firebase Console
2. Authentication > Users
3. Find user > Reset password
4. Send reset email

#### "Admin access required"

**Cause**: User account exists but lacks admin claim

**Solution**: Administrator must set admin claim (see above command)

**Verify claim is set**:
```powershell
# Check if claim is active
python -c "
import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate('path/to/firebase-key.json')
firebase_admin.initialize_app(cred)
user = auth.get_user_by_email('your-email@example.com')
print(user.custom_claims)  # Should show {'admin': True}
"
```

### Session Expires Quickly

**Symptoms**:
- Logged out after a few minutes
- Need to re-login frequently

**Solutions**:

1. **Check Firebase ID token expiration** (default: 1 hour)

2. **Implement token refresh** (if not already):
   - Token should refresh automatically
   - Check browser console for refresh errors

3. **Stay signed in**:
   - Ensure persistence is set to `LOCAL` in code
   - Check browser allows localStorage

### Firebase Authentication Errors

**Error**: `Firebase: Error (auth/network-request-failed)`

**Solutions**:
1. Check internet connection
2. Verify firewall isn't blocking Firebase
3. Check Firebase service status

**Error**: `Firebase: Error (auth/too-many-requests)`

**Solutions**:
1. Wait 15-30 minutes
2. Use password reset if locked out
3. Contact Firebase support for persistent issues

---

## Prediction Issues

### "Please enter a job description" Error

**Cause**: Empty textarea

**Solution**: Paste or type text before clicking Submit

### Rate Limit Exceeded

**Error**: `Rate limit exceeded: 10 per 1 minute`

**Solutions**:

1. **Wait 60 seconds** before next request

2. **Use bulk API** (for admins):
   - Contact admin for API key
   - Use programmatic access

3. **Increase limit** (admins only):
   - Edit `app/main.py`
   - Change rate limit decorator:
```python
@limiter.limit("20/minute")  # Increase from 10 to 20
```

### Predictions Return Errors

**Error**: `500 Internal Server Error`

**Diagnostic**:
```powershell
# Check server logs
# Look for traceback in terminal where uvicorn is running
```

**Common Causes & Fixes**:

1. **Model file missing**:
   - Check `m2_outputs/logreg_best.joblib` exists
   - Retrain model or restore from backup

2. **TF-IDF vectorizer missing**:
   - Check `m1_outputs/tfidf_vectorizer.pkl` exists
   - Run artifact generation script

3. **Memory error**:
   - Restart server
   - Reduce model size
   - Increase system memory

### Unexpected Prediction Results

**Symptoms**:
- Obviously fake job marked as real
- Obviously real job marked as fake
- Confidence always low

**Diagnostic Steps**:

1. **Check model metrics**:
```powershell
Invoke-RestMethod http://localhost:8000/model-info
```

2. **Test with known examples**:
   - Try example from documentation
   - Compare with expected results

**Solutions**:

1. **Flag incorrect prediction**:
   - Use Flag feature
   - Provide details

2. **Retrain model** (admins):
   - Accumulate 20+ validated flags
   - Trigger retraining

3. **Rollback model** (if recent retrain caused issue):
   - Select previous version
   - Click Rollback

---

## Admin Dashboard Issues

### Dashboard Not Loading

**Symptoms**:
- Blank admin page
- Loading spinner forever
- No data shown

**Solutions**:

1. **Check authentication**:
   - Verify logged in (see email in header)
   - Check admin claim is set

2. **Inspect network requests**:
   - F12 > Network tab
   - Look for failed `/admin/*` requests
   - Check response status codes

3. **Verify backend endpoints**:
```powershell
# Test endpoint directly (replace with your ID token)
$headers = @{ Authorization = "Bearer YOUR-ID-TOKEN" }
Invoke-RestMethod -Method GET -Headers $headers http://localhost:8000/admin/metrics/summary
```

4. **Check browser console** for JavaScript errors

### Metrics Not Updating

**Symptoms**:
- Numbers don't change
- Old data shown
- Refresh button doesn't work

**Solutions**:

1. **Manual refresh**:
   - Click Refresh button
   - Wait a few seconds

2. **Hard refresh page**:
```
Ctrl+Shift+R
```

3. **Check database has new data**:
```powershell
sqlite3 data/app.db "SELECT COUNT(*) FROM prediction_events;"
```

4. **Clear browser cache**:
   - Ctrl+Shift+Delete
   - Clear cached data

### Charts Not Displaying

**Symptoms**:
- Empty chart areas
- No donut or line chart
- Console errors about Chart.js

**Solutions**:

1. **Hard refresh**:
```
Ctrl+Shift+R
```

2. **Check Chart.js loads**:
   - F12 > Network tab
   - Look for Chart.js CDN request
   - Should be 200 OK

3. **Check internet connection** (Chart.js loads from CDN)

4. **Verify chart data**:
   - F12 > Console
   - Look for `renderStats` or `renderTrend` errors

5. **Check CSS height settings**:
   - Ensure `.chart-card { height: 250px }` in styles.css

---

## Model Management Issues

### Retraining Fails

**Error**: `Retraining failed`

**Diagnostic**:
```powershell
# Check server logs for detailed error
# Look in terminal running uvicorn
```

**Common Causes & Fixes**:

#### Insufficient Data

**Error**: Not enough samples to split

**Solution**:
- Need at least 10 validated flags
- Check validated flag count:
```powershell
sqlite3 data/app.db "SELECT COUNT(*) FROM flagged_posts WHERE status='validated';"
```

#### Missing Base Dataset

**Error**: `fake_job_postings.csv not found`

**Solution**:
- Ensure CSV file exists in project root
- Download from data source if missing
- Check file path in code

#### Permission Error

**Error**: Cannot write to `m2_outputs/` or `m2_versions/`

**Solution**:
```powershell
# Create directories with permissions
New-Item -ItemType Directory -Path m2_outputs -Force
New-Item -ItemType Directory -Path m2_versions -Force
```

#### Python Package Error

**Error**: `ImportError` or `ModuleNotFoundError`

**Solution**:
```powershell
# Reinstall scikit-learn
pip install --upgrade scikit-learn
```

### Rollback Not Working

**Symptoms**:
- Version doesn't change
- Error message shown
- Model still uses new version

**Solutions**:

1. **Verify version exists**:
```powershell
ls m2_versions/  # Should show version folders
ls m2_versions/2026-01-03_08-15-22/  # Should contain joblib and json files
```

2. **Check file permissions**:
```powershell
# Ensure write permissions on m2_outputs/
```

3. **Manual rollback**:
```powershell
Copy-Item m2_versions/2026-01-03_08-15-22/* m2_outputs/ -Force
# Restart server
```

4. **Check server logs** for specific error

### Model Version Not Listed

**Symptoms**:
- Dropdown shows no versions
- Old versions missing

**Solutions**:

1. **Check versions directory**:
```powershell
ls m2_versions/
```

2. **Verify folder structure**:
```
m2_versions/
  2026-01-04_11-30-45/
    logreg_best.joblib
    logreg_metrics.json
  2026-01-03_08-15-22/
    logreg_best.joblib
    logreg_metrics.json
```

3. **Refresh admin page**:
```
Ctrl+R
```

---

## Database Issues

### Database Locked

**Error**: `database is locked`

**Causes**:
- Multiple processes accessing SQLite simultaneously
- Long-running transaction
- Crashed process holding lock

**Solutions**:

1. **Restart server**:
```powershell
Stop-Process -Name python -Force
# Start server again
```

2. **Check for multiple server instances**:
```powershell
Get-Process python  # Should show only one uvicorn process
```

3. **Switch to PostgreSQL** for production:
```powershell
$env:DATABASE_URL = "postgresql+psycopg2://user:pass@localhost/dbname"
```

### Database Corruption

**Symptoms**:
- SQLite errors
- Data retrieval fails
- Integrity errors

**Solutions**:

1. **Check database integrity**:
```powershell
sqlite3 data/app.db "PRAGMA integrity_check;"
```

2. **Restore from backup**:
```powershell
Copy-Item backup/app.db data/app.db -Force
```

3. **Rebuild database**:
```powershell
# Backup first!
Copy-Item data/app.db data/app.db.backup

# Dump and reload
sqlite3 data/app.db .dump > dump.sql
Remove-Item data/app.db
sqlite3 data/app.db < dump.sql
```

### Missing Tables

**Error**: `no such table: flagged_posts`

**Solutions**:

1. **Reinitialize database**:
```python
# Run this Python script
from app.storage.db import Base, engine
Base.metadata.create_all(bind=engine)
```

2. **Or restart server** (auto-creates tables)

### Slow Queries

**Symptoms**:
- Dashboard loads slowly
- Exports timeout
- High CPU usage

**Solutions**:

1. **Analyze and optimize**:
```sql
sqlite3 data/app.db
ANALYZE;
```

2. **Add indexes** (if missing):
```sql
CREATE INDEX IF NOT EXISTS idx_flagged_status ON flagged_posts(status);
CREATE INDEX IF NOT EXISTS idx_prediction_timestamp ON prediction_events(timestamp DESC);
```

3. **Clean old data**:
```sql
DELETE FROM prediction_events WHERE timestamp < DATE('now', '-90 days');
VACUUM;
```

---

## Performance Issues

### High Memory Usage

**Symptoms**:
- Python process uses >1GB RAM
- Server becomes unresponsive
- Out of memory errors

**Diagnostic**:
```powershell
Get-Process python | Select-Object ProcessName,WS
```

**Solutions**:

1. **Restart server regularly**:
```powershell
# Daily restart recommended for production
Stop-Process -Name python -Force
# Start server
```

2. **Reduce batch sizes** in retraining

3. **Use lighter model** (if using BiLSTM, switch to LogReg only)

4. **Clean database** (remove old logs)

### High CPU Usage

**Symptoms**:
- CPU at 100%
- Server slow to respond
- Fan running loud

**Solutions**:

1. **Check for infinite loops** in logs

2. **Reduce worker count**:
```powershell
uvicorn app.main:app --workers 1  # Use single worker
```

3. **Optimize database queries** (add indexes)

4. **Monitor background tasks**:
   - Ensure retraining completes
   - Check for stuck tasks

### Slow Predictions

**Target**: <100ms per prediction  
**Acceptable**: 100-300ms  
**Slow**: >300ms

**Solutions**:

1. **Warm up model** (make dummy prediction on startup)

2. **Use model caching** (keep loaded in memory)

3. **Optimize TF-IDF** (reduce max_features if needed)

4. **Profile code**:
```python
import cProfile
cProfile.run('predict_function(text)')
```

---

## Network & API Issues

### CORS Errors

**Error**: `Access to fetch blocked by CORS policy`

**Solutions**:

1. **Set CORS_ALLOW_ORIGINS**:
```powershell
$env:CORS_ALLOW_ORIGINS = "http://localhost:8000,http://127.0.0.1:8000"
```

2. **Ensure frontend served from same origin** as backend

3. **Check CORS middleware** in `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Connection Refused

**Error**: `ERR_CONNECTION_REFUSED` or `ConnectionRefusedError`

**Solutions**:

1. **Check server is running**:
```powershell
netstat -ano | findstr :8000
```

2. **Verify correct port and host**:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

3. **Check firewall settings**:
   - Allow Python through firewall
   - Allow port 8000

4. **Try 127.0.0.1 instead of localhost**:
```
http://127.0.0.1:8000
```

### Timeout Errors

**Symptoms**:
- Requests timeout
- 504 Gateway Timeout
- No response

**Solutions**:

1. **Increase timeout** in API calls:
```javascript
// In frontend JavaScript
fetch(url, { timeout: 30000 })  // 30 seconds
```

2. **Optimize backend** to respond faster

3. **Check network latency**:
```powershell
ping localhost  # Should be <1ms
```

---

## Diagnostic Commands Reference

### Check System Status
```powershell
# Server running?
netstat -ano | findstr :8000

# Python process
Get-Process python

# Virtual environment active?
where python  # Should point to .venv

# Environment variables
$env:FIREBASE_CREDENTIALS
$env:DATABASE_URL

# Files exist?
Test-Path m2_outputs/logreg_best.joblib
Test-Path m1_outputs/tfidf_vectorizer.pkl
Test-Path data/app.db
```

### Test API Endpoints
```powershell
# Health check
Invoke-RestMethod http://localhost:8000/health

# Model info
Invoke-RestMethod http://localhost:8000/model-info

# Prediction
$body = @{ description = "Test job posting" } | ConvertTo-Json
Invoke-RestMethod -Method POST -ContentType "application/json" -Body $body http://localhost:8000/predict

# Admin endpoints (requires token)
$headers = @{ Authorization = "Bearer YOUR-TOKEN" }
Invoke-RestMethod -Method GET -Headers $headers http://localhost:8000/admin/metrics/summary
```

### Database Checks
```powershell
# Connect to database
sqlite3 data/app.db

# Check table sizes
SELECT COUNT(*) FROM prediction_events;
SELECT COUNT(*) FROM flagged_posts;
SELECT COUNT(*) FROM audit_logs;

# Check database size
ls data/app.db | Select-Object Length

# Integrity check
sqlite3 data/app.db "PRAGMA integrity_check;"
```

### Log Analysis
```powershell
# Run server with debug logging
uvicorn app.main:app --log-level debug

# Save logs to file
uvicorn app.main:app --log-level debug 2>&1 | Tee-Object -FilePath server.log
```

---

## Getting Help

### Information to Collect

When reporting issues, provide:

1. **Error message** (exact text or screenshot)
2. **Steps to reproduce**
3. **Expected vs actual behavior**
4. **Environment details**:
   - Python version (`python --version`)
   - OS version
   - Browser (if frontend issue)
5. **Relevant logs** (server output, browser console)
6. **Screenshots** (if UI issue)

### Contact Support

- **Email**: support@example.com (update with your email)
- **Include**: "TROUBLESHOOTING:" in subject line
- **Response time**: 24-48 hours

### Emergency Procedures

**Critical Issues** (production down):

1. **Restart server immediately**
2. **Check logs for errors**
3. **Rollback to last known good version**
4. **Contact emergency support**
5. **Document the incident**

**Data Loss**:

1. **Stop all operations**
2. **Restore from last backup**
3. **Verify data integrity**
4. **Document what was lost**
5. **Contact administrator**

---

**Document Version**: 1.0  
**Last Updated**: January 4, 2026  
**For More Help**: See FAQ and other documentation
