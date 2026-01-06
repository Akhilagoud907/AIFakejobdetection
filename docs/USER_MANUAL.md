# User Manual - Fake Job Detector

## Welcome

The Fake Job Detector helps you identify potentially fraudulent job postings using machine learning. Simply paste a job description and get an instant analysis.

---

## Getting Started

### Accessing the Application

1. Open your web browser
2. Navigate to: `http://localhost:8000` (or your deployed URL)
3. You'll see the main prediction interface

**No account or login required** for using the job detector!

---

## Using the Job Detector

### Step 1: Enter Job Description

1. Locate the **Job Description** text area on the page
2. Paste or type the complete job posting text
3. Include as much detail as possible for better accuracy:
   - Job title and responsibilities
   - Required qualifications
   - Company information
   - Salary and benefits
   - Application instructions

**Tip**: More detailed descriptions provide more accurate predictions!

### Step 2: Add Optional Information

Below the job description, you can provide additional details:

- **Company** (optional): Name of the hiring company
- **Location** (optional): Job location or "Remote"
- **Salary** (optional): Salary range or amount

These fields help improve prediction accuracy but are not required.

### Step 3: Submit for Analysis

Click the **Submit** button to analyze the job posting.

**Note**: You can also click **Load Example** to see a sample job posting.

### Step 4: View Results

After submission, you'll see the prediction results:

#### Real Job Posting ✓
```
┌──────────────────────────────┐
│  Classification: Real         │
│  Confidence: 92%              │
│  Processing Time: 45ms        │
└──────────────────────────────┘
```

- **Green badge**: Indicates a legitimate job posting
- **High confidence**: The model is confident in its prediction
- **Quick response**: Processing typically takes under 100ms

#### Fake Job Posting ✗
```
┌──────────────────────────────┐
│  Classification: Fake         │
│  Confidence: 87%              │
│  Processing Time: 42ms        │
└──────────────────────────────┘
```

- **Red badge**: Indicates a potentially fraudulent posting
- **High confidence**: The model has detected suspicious patterns
- **Warning**: Proceed with caution or avoid this job

#### Low Confidence Warning ⚠️
```
┌──────────────────────────────┐
│  Classification: Fake         │
│  Confidence: 52%              │
│  ⚠️ Warning: Low confidence   │
│  prediction. Please verify    │
│  manually.                    │
└──────────────────────────────┘
```

When confidence is below 60%, you'll see a warning:
- The model is uncertain about the prediction
- Use additional research to verify the job
- Trust your instincts and look for red flags

---

## Understanding Predictions

### What is Confidence?

Confidence represents how certain the model is about its prediction:

- **90-100%**: Very confident (highly reliable)
- **70-89%**: Confident (reliable)
- **60-69%**: Moderately confident (generally reliable)
- **Below 60%**: Low confidence (requires verification)

### Red Flags to Watch For

Even with "Real" predictions, be cautious if you see:

✗ **Unrealistic promises**
- "Earn $10,000/week from home!"
- "No experience required, high pay!"
- "Guaranteed income with no effort!"

✗ **Suspicious contact methods**
- Personal email addresses (Gmail, Yahoo)
- No company website or phone number
- Requests to contact via messaging apps only

✗ **Requests for money or personal info**
- "Send $50 for training materials"
- "Provide bank account for direct deposit setup"
- "Share your SSN/ID before interview"

✗ **Poor grammar and spelling**
- Multiple typos and errors
- Unprofessional language
- Generic job descriptions

✗ **Vague job details**
- No specific responsibilities
- "Various tasks" or "TBD"
- No company name or location

### Green Flags (Legitimate Jobs)

✓ **Detailed description**
- Clear job title and responsibilities
- Specific qualifications required
- Realistic salary range

✓ **Professional contact**
- Official company email domain
- Company website and phone
- LinkedIn company page

✓ **Standard process**
- Application through company website
- Multiple interview rounds
- Background check mentioned

✓ **Realistic requirements**
- Appropriate experience level
- Industry-standard compensation
- Clear working hours/conditions

---

## Flagging Suspicious Jobs

If you believe a prediction is incorrect or want to report a suspicious job, you can flag it for admin review.

### When to Flag

Flag a job posting if:
- The prediction seems wrong
- You know the job is fraudulent
- You've encountered this scam before
- You want to help improve the system

### How to Flag

1. After viewing a prediction, click the **Flag This Result** button
2. A flag submission form will appear
3. Select a reason for flagging:
   - **Too good to be true**: Unrealistic promises
   - **Suspicious contact**: Unusual contact methods
   - **Phishing**: Attempts to steal information
   - **Other**: Any other concerns

4. (Optional) Add comments explaining your concern
5. Click **Submit Flag**

### After Flagging

- You'll see a confirmation message
- Admin team will review your flag
- Validated flags help retrain and improve the model
- Your contribution helps protect other users!

---

## Tips for Best Results

### ✓ Do's

- **Paste complete job descriptions**: Include all available text
- **Include metadata**: Add company, location, salary if known
- **Check multiple sources**: Verify jobs through official channels
- **Use common sense**: Trust your instincts about suspicious postings
- **Report frauds**: Flag jobs you know are fake

### ✗ Don'ts

- **Don't paste partial descriptions**: May reduce accuracy
- **Don't rely solely on predictions**: Use as one of many tools
- **Don't share personal info**: Never provide sensitive data before verification
- **Don't skip research**: Always investigate the company independently
- **Don't trust perfect offers**: If it seems too good to be true, it probably is

---

## Examples

### Example 1: Legitimate Software Engineer Position

**Input**:
```
Senior Software Engineer

Acme Technologies is seeking an experienced software engineer to join 
our platform team. 

Responsibilities:
- Design and develop scalable web applications
- Collaborate with product managers and designers
- Mentor junior engineers
- Participate in code reviews and architecture decisions

Requirements:
- 5+ years of software development experience
- Strong knowledge of Python, JavaScript, and SQL
- Experience with cloud platforms (AWS/Azure/GCP)
- Bachelor's degree in Computer Science or related field

Benefits:
- Competitive salary ($120,000 - $150,000)
- Health insurance and 401(k)
- Flexible work arrangements
- Professional development budget

To apply, visit our careers page: careers.acme.com
```

**Expected Result**: **Real** with high confidence (85-95%)

### Example 2: Suspicious Work-from-Home Offer

**Input**:
```
URGENT - Data Entry Specialist

Make $5000-$8000 per month working from home!!!

No experience needed! Just need basic computer skills and internet.

Flexible hours - work whenever you want!
Get paid weekly via PayPal or bank transfer.

To apply, send your resume and copy of ID to:
hiringmanager2024@gmail.com

Limited positions available - apply NOW!!!
```

**Expected Result**: **Fake** with high confidence (80-95%)

### Example 3: Ambiguous Posting (Low Confidence)

**Input**:
```
Marketing position available. Good opportunity for motivated individual.
Contact for details.
```

**Expected Result**: Could be Real or Fake with low confidence (50-60%)
- Too vague to make confident prediction
- Requires additional research

---

## Mobile Usage

The Fake Job Detector works on mobile devices:

1. **Responsive design**: Adapts to phone/tablet screens
2. **Touch-friendly**: Large buttons and input areas
3. **Fast performance**: Quick predictions on mobile data

**Tip**: Use copy/paste from job websites or apps!

---

## Browser Compatibility

Supported browsers:
- ✓ Google Chrome (recommended)
- ✓ Mozilla Firefox
- ✓ Microsoft Edge
- ✓ Safari
- ✓ Opera

**Note**: Internet Explorer is not supported.

---

## Privacy & Security

### What Data is Collected?

When you submit a job description:
- Job description text is analyzed (not stored permanently)
- Prediction result is logged (without personal info)
- Your IP address is hashed for rate limiting (cannot be traced back)

### What is NOT Collected?

- No personal information
- No account creation required
- No tracking cookies
- No email addresses
- No browsing history

### Data Usage

- Prediction logs help improve the model
- Flagged posts are reviewed by admins
- No data is sold to third parties
- Compliant with privacy regulations

---

## Troubleshooting

### "Please enter a job description"
- **Cause**: Submitted empty form
- **Solution**: Paste or type a job description before clicking Submit

### "Rate limit exceeded"
- **Cause**: Too many requests in short time (10 per minute)
- **Solution**: Wait 60 seconds and try again

### Slow predictions
- **Cause**: Server overload or network issues
- **Solution**: Refresh page and retry, or try later

### Unexpected results
- **Cause**: Model limitations or edge cases
- **Solution**: Use Flag feature to report, verify through other sources

### Page not loading
- **Cause**: Server down or network issues
- **Solution**: Check internet connection, try different browser, contact support

---

## Getting Help

### Need Assistance?

- **Technical issues**: Check the Troubleshooting section
- **Incorrect predictions**: Use the Flag feature
- **General questions**: See the FAQ section

### Contact

For urgent issues or feedback:
- Email: support@example.com (update with your support email)
- Response time: 24-48 hours

---

## Best Practices for Job Seekers

### Before Applying to Any Job:

1. **Research the company**
   - Check official website
   - Look for reviews on Glassdoor
   - Verify company exists and is legitimate

2. **Use multiple verification methods**
   - Google the job description (check for scam reports)
   - Search company on Better Business Bureau
   - Look for company on LinkedIn

3. **Trust your instincts**
   - If something feels off, it probably is
   - Don't let urgency pressure you
   - Legitimate companies won't rush you

4. **Protect your information**
   - Never pay fees for job applications
   - Don't provide SSN/bank info before hire
   - Use a separate email for job searching

5. **Verify interview requests**
   - Real interviews are via phone/video/in-person
   - Beware of text-only "interviews"
   - Research interviewer on LinkedIn

### Red Flags Checklist

Before applying, check for these warning signs:

- [ ] No company website or fake website
- [ ] Generic email (Gmail, Yahoo, Hotmail)
- [ ] Requests money for training/equipment
- [ ] Guaranteed high income with no experience
- [ ] Poor grammar and spelling errors
- [ ] Urgent hiring with immediate start
- [ ] No interview process mentioned
- [ ] Vague job description
- [ ] Requests personal/financial info upfront
- [ ] Found only on sketchy job boards

**If you checked 3+ boxes, proceed with extreme caution!**

---

## Frequently Asked Questions

### How accurate is the detector?

The model achieves ~98% accuracy on test data. However, new scam patterns may not be detected immediately. Always verify jobs independently.

### Can I use this for bulk analysis?

The public interface is for individual job postings. For bulk analysis, contact us about API access.

### Does this work for all types of jobs?

Yes! The model is trained on various industries and job types, from entry-level to executive positions.

### What if I disagree with a prediction?

Use the Flag feature to report it. Admin review helps improve the model over time.

### Is my data stored?

Job descriptions are processed in memory and not permanently stored. Only prediction statistics (fake/real count, confidence) are logged.

### Can I integrate this into my website?

Yes! Contact us about API access and integration options.

---

## Updates and Improvements

The Fake Job Detector is continuously improved:

- **Model retraining**: Regularly updated with new data
- **New features**: Based on user feedback
- **Performance improvements**: Faster predictions
- **Accuracy enhancements**: Better detection of new scam types

Check back for updates and new capabilities!

---

## Feedback

We value your feedback!

**Help us improve by**:
- Flagging incorrect predictions
- Reporting new scam patterns
- Suggesting new features
- Sharing your experience

Your input makes the system better for everyone.

---

**Document Version**: 1.0  
**Last Updated**: January 4, 2026  
**For Admin Features**: See Admin Panel Guide

---

## Legal Disclaimer

This tool is provided as-is for informational purposes. While we strive for accuracy, the Fake Job Detector should not be your only method of verifying job postings. Always conduct thorough research before applying to any job or sharing personal information. We are not liable for any losses or damages resulting from reliance on predictions made by this tool.
