# Admin Panel Guide

## Overview

The Admin Dashboard provides powerful tools for monitoring predictions, managing flagged content, and maintaining the machine learning model. This guide covers all administrative features and operations.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Dashboard Overview](#dashboard-overview)
4. [Metrics & Analytics](#metrics--analytics)
5. [Managing Flagged Posts](#managing-flagged-posts)
6. [Model Management](#model-management)
7. [Data Exports](#data-exports)
8. [Activity Monitoring](#activity-monitoring)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Admin Dashboard

1. Navigate to: `http://localhost:8000/admin` (or your deployed URL)
2. You'll see the admin login page
3. Sign in with your authorized admin account

### System Requirements

- Modern web browser (Chrome, Firefox, Edge, Safari)
- Admin account with Firebase authentication
- Admin custom claim (`admin: true`) set in Firebase

---

## Authentication

### Logging In

1. **Enter your email address**: Use the email registered in Firebase
2. **Enter your password**: Your Firebase account password
3. **Click "Login"**

After successful login:
- Dashboard loads automatically
- Your email appears in the header
- You'll see real-time metrics

### Creating an Admin Account

**Note**: Admin accounts must be created by system administrators.

**Step 1: Sign Up** (First Time Only)
1. Click "Sign Up" link on login page
2. Enter email and password
3. Confirm password
4. Click "Sign Up"

**Step 2: Set Admin Claim** (Requires Backend Access)
```powershell
# Run this command on the server
$env:FIREBASE_CREDENTIALS="path/to/service-account.json"

C:/path/to/.venv/Scripts/python.exe -c "
import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate('path/to/service-account.json')
firebase_admin.initialize_app(cred)

user = auth.get_user_by_email('admin@example.com')
auth.set_custom_user_claims(user.uid, {'admin': True})
print('Admin claims set for', user.email)
"
```

### Logging Out

Click the **Logout** button in the top-right corner.

### Authentication Errors

See [Troubleshooting](#troubleshooting) section for common issues:
- "No account found with this email"
- "Incorrect password"
- "Admin access required"

---

## Dashboard Overview

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Admin Dashboard                    user@example.com [Logout]│
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │Total Predict │ │    Fake      │ │    Real      │        │
│  │     1523     │ │     234      │ │    1289      │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                               │
│  ┌──────────────┐                                            │
│  │Flags Pending │                                            │
│  │      12      │                                            │
│  └──────────────┘                                            │
│                                                               │
│  ┌─────────────────────────┐ ┌─────────────────────────┐   │
│  │   Distribution Chart    │ │    Trend Chart          │   │
│  │   (Donut: Fake vs Real) │ │    (Line: Daily counts) │   │
│  └─────────────────────────┘ └─────────────────────────┘   │
│                                                               │
│  [Refresh] [Retrain Model]            [Select version ▼]     │
│  [Rollback]                                                   │
│                                                               │
│  [Start Date] [End Date] [Export Predictions CSV]            │
│  [Export Flags CSV] [PDF Report]                             │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Flagged Posts                             │ │
│  │  ID | Prediction | Reason  | Status | Actions        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Recent Activity                           │ │
│  │  ID | Prediction | Confidence | Latency | Timestamp  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Sections

1. **Metrics Cards**: Summary statistics at a glance
2. **Charts**: Visual representation of data
3. **Controls**: Actions for model and data management
4. **Flagged Posts**: User-reported suspicious jobs
5. **Recent Activity**: Latest prediction logs

---

## Metrics & Analytics

### Summary Metrics

Located at the top of the dashboard:

#### Total Predictions
- **What it shows**: Total number of job postings analyzed
- **Updates**: Real-time when page refreshes
- **Use case**: Track system usage and growth

#### Fake Count
- **What it shows**: Number of jobs classified as fake
- **Color**: Red (indicates fraudulent content)
- **Use case**: Monitor fraud prevalence

#### Real Count
- **What it shows**: Number of jobs classified as real
- **Color**: Green (indicates legitimate content)
- **Use case**: Assess overall job quality in dataset

#### Flags (Pending)
- **What it shows**: Number of flagged posts awaiting review
- **Color**: Orange (indicates action needed)
- **Use case**: Track workload for admin review

### Distribution Chart (Donut)

**Visual**: Circular chart showing Fake vs Real ratio

**Interpretation**:
- **Larger red section**: More fake jobs detected
- **Larger green section**: More legitimate jobs processed
- **Balanced**: Equal distribution

**Use cases**:
- Assess overall data quality
- Identify trends in job market
- Monitor system effectiveness

### Trend Chart (Line Graph)

**Visual**: Multi-line time-series graph

**Lines**:
- **Blue line**: Total predictions per day
- **Red line**: Fake predictions per day

**Features**:
- **X-axis**: Dates (last 7 days by default)
- **Y-axis**: Prediction count
- **Hover**: Shows exact numbers

**Use cases**:
- Identify usage patterns (busy days/times)
- Spot anomalies (sudden spikes)
- Track growth over time
- Compare fake vs real trends

### Refreshing Metrics

Click the **Refresh** button to update all metrics and charts with latest data.

**Auto-refresh**: Consider refreshing every 5-10 minutes for real-time monitoring.

---

## Managing Flagged Posts

### Viewing Flagged Posts

The Flagged Posts table shows user-reported suspicious jobs.

**Columns**:
- **ID**: Unique flag identifier
- **Prediction**: Model's classification (Fake/Real)
- **Reason**: Why user flagged it
- **Status**: Current review status
- **Confidence**: Model confidence score
- **Timestamp**: When it was flagged
- **Actions**: Buttons for admin review

### Status Values

| Status | Color | Meaning |
|--------|-------|---------|
| **Pending** | Orange | Awaiting admin review |
| **Validated** | Green | Admin confirmed label, used in retraining |
| **Dismissed** | Red | Admin rejected flag, not used in retraining |

### Reviewing a Flagged Post

**Step 1: Read the details**
- Check the prediction and confidence
- Review the reason provided by user
- Read any additional comments

**Step 2: Make a decision**

Choose one of three actions:

#### Option A: Mark as Fake
1. Click **Mark Fake** button
2. System sets `validated_label = 1`
3. Status changes to **Validated**
4. Post will be used in next retraining

**When to use**:
- You verify the job is fraudulent
- Prediction was correct (Fake → Fake)
- Prediction was incorrect (Real → Fake, user was right)

#### Option B: Mark as Real
1. Click **Mark Real** button
2. System sets `validated_label = 0`
3. Status changes to **Validated**
4. Post will be used in next retraining

**When to use**:
- You verify the job is legitimate
- Prediction was correct (Real → Real)
- Prediction was incorrect (Fake → Real, false positive)

#### Option C: Dismiss
1. Click **Dismiss** button
2. Status changes to **Dismissed**
3. Post will NOT be used in retraining

**When to use**:
- Insufficient information to verify
- Spam or irrelevant flag
- Duplicate flag
- User error

### Best Practices for Review

✓ **Do Research**:
- Google the company name
- Check company website
- Look for similar scam reports
- Verify contact information

✓ **Look for Patterns**:
- Compare with known scams
- Check for red flags (unrealistic pay, urgency)
- Assess professionalism

✓ **Be Consistent**:
- Apply same criteria to all reviews
- Document your reasoning (mental note)
- Consult with team on edge cases

✗ **Don't**:
- Rush through reviews
- Validate without verification
- Dismiss genuine concerns
- Let personal bias influence decisions

### Bulk Review Tips

For reviewing multiple flags:
1. Sort by status (pending first)
2. Group similar reasons together
3. Review in batches of 10-20
4. Take breaks to maintain focus
5. Track your decisions

---

## Model Management

### Understanding Model Retraining

**Purpose**: Improve model accuracy using validated flagged posts.

**Process**:
1. System loads base dataset (`fake_job_postings.csv`)
2. Adds validated flagged posts with confirmed labels
3. Splits data into training and test sets
4. Trains new Logistic Regression model
5. Evaluates metrics (accuracy, precision, recall, F1)
6. Saves versioned artifacts
7. Activates new model

**Duration**: Typically 30-60 seconds depending on data size.

### Triggering Retraining

**Step 1: Prepare**
- Ensure you have validated flags (at least 10-20 recommended)
- Check that no retraining is currently running
- Notify team if in production (may cause brief slowdown)

**Step 2: Initiate**
1. Click **Retrain Model** button
2. Confirmation appears: "Retraining started"
3. Status indicator shows "running"

**Step 3: Monitor**
- Status updates automatically
- Watch for "succeeded" or "failed"
- Check logs if retraining fails

### Checking Retrain Status

**Current Status Indicator**:
- **Green badge "succeeded"**: Last retrain completed successfully
- **Orange badge "running"**: Retraining in progress
- **Red badge "failed"**: Last retrain encountered error

**Status Details**:
- Shows timestamp of last operation
- Indicates model version created
- Displays any error messages

### Model Versions

**Version Format**: `YYYY-MM-DD_HH-MM-SS` (e.g., `2026-01-04_11-30-45`)

**Viewing Versions**:
1. Click dropdown menu labeled "Select version"
2. List shows all saved model versions (newest first)
3. Currently active version is highlighted

**Version Storage**:
- Versions saved in `m2_versions/` directory
- Active model in `m2_outputs/` directory
- Each version includes:
  - `logreg_best.joblib` (model file)
  - `logreg_metrics.json` (performance metrics)

### Rolling Back a Model

**When to Rollback**:
- New model performs worse than previous
- Retraining introduced errors
- Need to revert to stable version
- Testing/debugging purposes

**Step 1: Select Version**
1. Click "Select version" dropdown
2. Choose the version to rollback to
3. Note: Cannot rollback to current version

**Step 2: Execute Rollback**
1. Click **Rollback** button
2. Confirmation message appears
3. System copies selected version to active location
4. Model reloads automatically

**Step 3: Verify**
1. Check model info reflects old version
2. Test a few predictions
3. Monitor for expected behavior

**Caution**: Rollback is immediate and affects all users!

### Monitoring Model Performance

**Check metrics after retraining**:
1. Navigate to API docs: `http://localhost:8000/docs`
2. Try `/model-info` endpoint
3. Compare metrics:
   - **Accuracy**: Overall correctness (target: >95%)
   - **Precision**: Fake predictions that are actually fake (target: >90%)
   - **Recall**: Actual fakes that were caught (target: >95%)
   - **F1 Score**: Balance of precision and recall (target: >92%)

**Red flags** (consider rollback):
- Accuracy drops below 90%
- Precision significantly lower than previous
- F1 score decreased
- Many user complaints about predictions

---

## Data Exports

### Date Range Selection

Before exporting, optionally set date filters:

1. **Start Date/Time**:
   - Click first date input field
   - Select date from calendar
   - Set time (hours:minutes)
   - Format: YYYY-MM-DD HH:MM

2. **End Date/Time**:
   - Click second date input field
   - Select date from calendar
   - Set time (hours:minutes)
   - Format: YYYY-MM-DD HH:MM

**Note**: If dates are not set, export includes all data.

### Export Predictions CSV

**Purpose**: Export all prediction events for analysis.

**Step 1: Set filters** (optional)
- Start date: `2026-01-01 00:00`
- End date: `2026-01-04 23:59`

**Step 2: Click "Export Predictions CSV"**

**Step 3: Download file**
- Browser saves file: `predictions_YYYY-MM-DD.csv`
- Location: Your browser's download folder

**File Contents**:
```csv
id,prediction,confidence,latency_ms,timestamp
1,1,0.8743,45,2026-01-04T10:15:30
2,0,0.9123,38,2026-01-04T10:16:45
...
```

**Columns**:
- `id`: Unique prediction ID
- `prediction`: 0 (real) or 1 (fake)
- `confidence`: Confidence score (0-1)
- `latency_ms`: Processing time in milliseconds
- `timestamp`: ISO 8601 timestamp

**Use cases**:
- Data analysis in Excel/Python
- Creating custom reports
- Archiving historical data
- Performance monitoring

### Export Flags CSV

**Purpose**: Export flagged posts for review or training data.

**Process**: Same as predictions export

**File Contents**:
```csv
id,prediction,reason,status,confidence,timestamp,validated_label
42,1,phishing,pending,0.8234,2026-01-04T09:30:15,
43,1,too_good_to_be_true,validated,0.7654,2026-01-03T14:22:10,1
...
```

**Columns**:
- `id`: Flag ID
- `prediction`: Model prediction
- `reason`: User-reported reason
- `status`: Current status
- `confidence`: Model confidence
- `timestamp`: When flagged
- `validated_label`: Admin-confirmed label (empty if not validated)

**Use cases**:
- Quality assurance
- Training data extraction
- User feedback analysis
- Reporting to stakeholders

### Generate PDF Report

**Purpose**: Create formatted summary report for stakeholders.

**Step 1: Set date range** (optional)
- Same as CSV exports

**Step 2: Click "PDF Report"**

**Step 3: Download report**
- Browser saves: `report_YYYY-MM-DD.pdf`

**Report Contents**:
- Executive summary
- Key metrics (total, fake, real, flags)
- Period covered (date range)
- Charts and visualizations
- Top flagged reasons
- Model performance metrics

**Use cases**:
- Monthly/quarterly reports
- Stakeholder presentations
- Compliance documentation
- Performance reviews

### Export Tips

✓ **Best Practices**:
- Export regularly (weekly/monthly backups)
- Use date ranges for large datasets
- Store exports securely
- Document export purposes
- Review exports for accuracy

✗ **Avoid**:
- Exporting without purpose
- Leaving exports unsecured
- Ignoring privacy regulations
- Sharing raw data externally

---

## Activity Monitoring

### Recent Activity Table

Shows the latest prediction events.

**Columns**:
- **ID**: Event identifier
- **Prediction**: Fake (1) or Real (0)
- **Confidence**: Model confidence (0-1 scale)
- **Latency**: Processing time in milliseconds
- **Timestamp**: When prediction was made

**Default**: Shows last 50 events

**Auto-updates**: When you click Refresh

### Use Cases

**Performance Monitoring**:
- Check latency (should be <100ms typically)
- Monitor confidence levels
- Identify slow predictions

**Usage Tracking**:
- See prediction frequency
- Identify peak usage times
- Track system load

**Quality Assurance**:
- Spot unusual patterns
- Verify predictions make sense
- Check for errors

### Interpreting Activity

**Healthy System**:
- Latency: 20-80ms consistently
- Confidence: Mostly 70%+ scores
- Predictions: Mix of fake and real
- No errors or failures

**Potential Issues**:
- Latency: Consistently >200ms (performance problem)
- Confidence: Many scores <60% (model needs retraining)
- Predictions: All same class (data imbalance?)
- Errors: 500 status codes (server issues)

---

## Best Practices

### Daily Operations

**Morning Checklist**:
- [ ] Log in to admin dashboard
- [ ] Review overnight metrics
- [ ] Check for pending flags
- [ ] Monitor system status
- [ ] Review any alerts/errors

**Throughout the Day**:
- [ ] Process new flagged posts
- [ ] Monitor prediction trends
- [ ] Respond to user reports
- [ ] Check system performance

**End of Day**:
- [ ] Final flag review
- [ ] Export daily data (optional)
- [ ] Document any issues
- [ ] Plan next day's tasks

### Weekly Tasks

- [ ] **Monday**: Review previous week's metrics
- [ ] **Wednesday**: Retrain model (if 20+ validated flags)
- [ ] **Friday**: Generate weekly report, export data

### Monthly Tasks

- [ ] Generate monthly PDF report
- [ ] Analyze long-term trends
- [ ] Review model performance
- [ ] Plan improvements
- [ ] Archive old data

### Security Best Practices

✓ **Password Security**:
- Use strong, unique password
- Enable 2FA in Firebase (if available)
- Never share credentials
- Change password quarterly

✓ **Access Control**:
- Log out when finished
- Don't leave dashboard open
- Use private/incognito on shared computers
- Report suspicious activity

✓ **Data Privacy**:
- Handle flagged content responsibly
- Don't share user reports publicly
- Follow data retention policies
- Comply with privacy regulations

### Performance Optimization

**Keep System Running Smoothly**:
1. Retrain model regularly (weekly recommended)
2. Review and process flags promptly
3. Export and archive old data
4. Monitor latency trends
5. Report persistent issues

---

## Troubleshooting

### Authentication Issues

#### "No account found with this email. Please sign up for a new account."
**Cause**: Email not registered in Firebase  
**Solution**:
1. Click "Sign Up" to create account
2. Contact administrator to set admin claims

#### "Incorrect password. Please try again."
**Cause**: Wrong password entered  
**Solution**:
1. Double-check password
2. Use password reset if forgotten
3. Check caps lock is off

#### "Admin access required"
**Cause**: User account doesn't have admin custom claim  
**Solution**:
1. Contact system administrator
2. Admin must run command to set `admin: true` claim
3. Log out and log back in after claim is set

### Dashboard Issues

#### Metrics not loading
**Cause**: API connection failure  
**Solution**:
1. Check network connection
2. Verify backend server is running
3. Check browser console for errors (F12)
4. Refresh page (Ctrl+R)

#### Charts not displaying
**Cause**: Chart.js library not loaded or data issue  
**Solution**:
1. Hard refresh (Ctrl+Shift+R)
2. Check browser console for errors
3. Clear browser cache
4. Try different browser

#### "Rate limit exceeded"
**Cause**: Too many requests (shouldn't happen for admin)  
**Solution**:
1. Wait 60 seconds
2. Refresh page
3. Report issue if persistent

### Flag Management Issues

#### Cannot update flag status
**Cause**: API error or authentication issue  
**Solution**:
1. Refresh ID token (log out and back in)
2. Check network connection
3. Verify backend is running
4. Check browser console for specific error

#### Flags not appearing
**Cause**: No flags submitted or database issue  
**Solution**:
1. Verify flags exist (check database or use public interface to create test flag)
2. Refresh dashboard
3. Check filter/status settings

### Model Management Issues

#### Retrain button does nothing
**Cause**: JavaScript error or API failure  
**Solution**:
1. Check browser console (F12)
2. Verify backend is running
3. Check retrain status endpoint manually
4. Refresh page and retry

#### Retraining fails
**Cause**: Insufficient data, file permissions, or code error  
**Solution**:
1. Check you have validated flags
2. Verify `fake_job_postings.csv` exists
3. Check server logs for error details
4. Ensure write permissions for `m2_outputs/` and `m2_versions/`

#### Rollback not working
**Cause**: Version doesn't exist or file error  
**Solution**:
1. Verify version exists in `m2_versions/` directory
2. Check file permissions
3. Try different version
4. Check server logs

### Export Issues

#### Date picker not working
**Cause**: Browser compatibility or JavaScript error  
**Solution**:
1. Use Chrome/Firefox (best compatibility)
2. Type date manually in format: `2026-01-04T10:30`
3. Leave empty to export all data

#### Export downloads empty file
**Cause**: No data in date range or API error  
**Solution**:
1. Expand date range
2. Remove date filters to export all
3. Check network tab in browser (F12)
4. Verify backend is running

#### PDF report generation fails
**Cause**: PDF library issue or data error  
**Solution**:
1. Try CSV export instead
2. Check server logs for error
3. Report issue to developer

### Performance Issues

#### Slow dashboard loading
**Cause**: Large dataset or server performance  
**Solution**:
1. Archive old data
2. Use date filters on exports
3. Increase server resources
4. Optimize database queries

#### High latency in activity log
**Cause**: Server overload or inefficient model  
**Solution**:
1. Check server CPU/memory usage
2. Optimize model if needed
3. Consider model caching improvements
4. Scale server resources

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+R` or `F5` | Refresh page |
| `Ctrl+Shift+R` | Hard refresh (clears cache) |
| `F12` | Open browser developer tools |
| `Ctrl+Shift+Delete` | Clear browser data |

---

## Glossary

**Confidence**: Probability score (0-100%) indicating model's certainty  
**Flag**: User report of suspicious job posting  
**Latency**: Time taken to process prediction (milliseconds)  
**Prediction**: Model's classification (fake or real)  
**Retrain**: Process of updating model with new data  
**Rollback**: Reverting to previous model version  
**Validated**: Admin-confirmed ground truth label  
**Version**: Timestamped model artifact  

---

## Support

### Getting Help

**For technical issues**:
- Check this guide's Troubleshooting section
- Review server logs
- Contact development team

**For operational questions**:
- Refer to Best Practices section
- Consult with other admins
- Review audit logs

**For urgent issues**:
- Email: admin-support@example.com (update with your support email)
- Response time: 2-4 hours during business hours

### Reporting Bugs

When reporting issues, include:
1. What you were trying to do
2. What happened instead
3. Steps to reproduce
4. Browser and OS version
5. Screenshots if applicable
6. Console errors (F12 > Console tab)

---

**Document Version**: 1.0  
**Last Updated**: January 4, 2026  
**For User Features**: See User Manual  
**For API Details**: See API Documentation
