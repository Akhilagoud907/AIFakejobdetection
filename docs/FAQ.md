# Frequently Asked Questions (FAQ)

## General Questions

### What is the Fake Job Detector?

The Fake Job Detector is a machine learning-powered web application that analyzes job postings to identify potentially fraudulent listings. It uses natural language processing and classification algorithms to assess job descriptions and flag suspicious patterns commonly found in scam postings.

### How does it work?

1. You paste a job description into the system
2. The text is processed and converted into numerical features using TF-IDF
3. A trained machine learning model (Logistic Regression) analyzes these features
4. The system returns a classification (Fake or Real) with a confidence score
5. The entire process typically takes 20-80 milliseconds

### How accurate is the detector?

The model achieves approximately **98% accuracy** on test data, with:
- **Precision**: ~96% (when it says "fake", it's correct 96% of the time)
- **Recall**: ~98% (catches 98% of actual fake jobs)
- **F1 Score**: ~97% (balanced performance)

However, new scam patterns may not be detected immediately. Always verify jobs through multiple sources.

### Is it free to use?

Yes! The public job detector interface is completely free with no account required. There are rate limits (10 predictions per minute) to prevent abuse.

### Do I need to create an account?

No account is needed for the public prediction interface. Only administrators need Firebase accounts to access the admin dashboard.

---

## Using the System

### What information do I need to provide?

**Required**:
- Job description (the more complete, the better)

**Optional** (helps improve accuracy):
- Company name
- Job location
- Salary range

### How long does a prediction take?

Predictions typically complete in **20-80 milliseconds**. Factors affecting speed:
- Length of job description
- Server load
- Network latency

### Can I check multiple jobs at once?

The web interface is designed for one job at a time. For bulk analysis, contact the administrator about API access.

### What if I don't have the complete job description?

Partial descriptions can still be analyzed, but:
- Accuracy may be reduced
- Confidence scores will likely be lower
- You may see a warning message

For best results, provide the complete job posting including:
- Job title and responsibilities
- Requirements and qualifications
- Company information
- Salary and benefits
- Application process

### Does it work for international jobs?

Yes! The model is trained on diverse job postings including international positions. However:
- Best performance on English-language postings
- May have lower accuracy for non-English jobs
- Cultural differences in job posting styles may affect predictions

---

## Understanding Results

### What does the confidence score mean?

Confidence represents how certain the model is about its prediction:

| Range | Interpretation |
|-------|---------------|
| **90-100%** | Very high confidence - highly reliable |
| **70-89%** | High confidence - reliable |
| **60-69%** | Moderate confidence - generally reliable |
| **Below 60%** | Low confidence - verify manually |

### What should I do with a low confidence prediction?

When confidence is below 60%:
1. **Don't rely solely on the prediction**
2. **Conduct additional research**:
   - Google the company
   - Check company website
   - Look for reviews on Glassdoor
   - Search for scam reports
3. **Look for red flags manually**
4. **Use the Flag feature** if you believe the prediction is wrong
5. **Trust your instincts**

### Can the system make mistakes?

Yes, like any machine learning system, it can make errors:

**False Positives**: Legitimate jobs marked as fake
- More common with unusual but legitimate opportunities
- Often have lower confidence scores
- Example: Legitimate startups with unconventional offerings

**False Negatives**: Fake jobs marked as real
- Happens with new scam patterns not in training data
- Sophisticated scams designed to appear legitimate
- Example: Well-written scams mimicking real companies

This is why we recommend using the detector as ONE tool among many for job verification.

### What's the difference between "Fake" and "Real"?

**Fake (Fraudulent)**:
- Job posting is likely a scam
- May be attempting phishing, identity theft, or advance fee fraud
- Common red flags detected (unrealistic pay, suspicious contact, etc.)

**Real (Legitimate)**:
- Job posting appears to be genuine
- Patterns match legitimate job descriptions
- No obvious red flags detected

**Important**: "Real" doesn't guarantee the job is perfect or that you should apply - always do your own research!

---

## Flagging Content

### When should I flag a job posting?

Flag a posting when:
- **Prediction seems incorrect** (you have evidence)
- **You know it's fraudulent** (personal experience or verification)
- **You encountered this scam** (can confirm it's fake)
- **You have additional information** that might help

### What happens when I flag something?

1. Your flag is saved to the database with status "pending"
2. Admin team receives the flag for review
3. Admin investigates and marks it as validated or dismissed
4. Validated flags are used to retrain and improve the model
5. You're helping make the system better for everyone!

### Can I see what happened to my flag?

Currently, there's no public tracking system for individual flags. The flag is reviewed by admins and may be used to improve the model in future updates.

### What information should I include when flagging?

**Required**:
- Reason for flagging (select from dropdown)

**Recommended**:
- Additional comments explaining your concern
- How you know it's fake (if applicable)
- Any evidence or links

More information helps admins make better decisions!

---

## Privacy & Security

### What data does the system collect?

**When you make a prediction**:
- Job description text (processed, not permanently stored)
- Optional metadata (company, location, salary)
- Hashed IP address (for rate limiting, cannot be traced back)
- Prediction result and confidence
- Timestamp and latency

**What is NOT collected**:
- Your name or email
- Personal information
- Browsing history
- Device information
- Location (beyond IP hash for rate limits)

### Is my data stored permanently?

- **Job descriptions**: Processed in memory, not permanently stored
- **Prediction logs**: Stored for 90 days for analytics, then deleted
- **Flagged content**: Stored indefinitely (for model improvement)
- **Audit logs**: Stored for 1 year (admin actions only)

### Can others see what I've checked?

No. Each prediction is anonymous and independent. There's no user account linking your predictions together.

### Is it safe to paste job descriptions?

Yes, but be aware:
- If a job description contains personal information (yours or someone else's), that could be flagged along with it
- Don't paste content that violates privacy or confidentiality agreements
- The system doesn't validate or sanitize PII - use discretion

### How is my IP address used?

Your IP address is:
1. Hashed with a cryptographic salt (one-way, cannot be reversed)
2. Used only for rate limiting (preventing abuse)
3. Not stored in plain text
4. Cannot be traced back to you
5. Automatically deleted after 90 days

---

## Technical Questions

### What technology powers the system?

**Frontend**:
- HTML5, CSS3, JavaScript
- Chart.js for visualizations
- Firebase SDK for authentication

**Backend**:
- Python 3.10+
- FastAPI web framework
- SQLAlchemy ORM
- SQLite/PostgreSQL database

**Machine Learning**:
- Scikit-learn (Logistic Regression)
- TF-IDF vectorization
- Optional: TensorFlow (BiLSTM model)

### What is TF-IDF?

**TF-IDF** (Term Frequency-Inverse Document Frequency) is a numerical statistic that:
- Converts text into numbers that machine learning models can understand
- Identifies important words in a document
- Weighs words by how unique they are across all documents

In simple terms: it helps the model understand which words in a job description are most significant for determining if it's fake.

### What machine learning model is used?

**Primary Model**: **Logistic Regression**
- Fast predictions (~40ms average)
- Highly accurate (~98%)
- Easy to interpret and maintain
- Works well with TF-IDF features

**Optional Model**: **BiLSTM** (Bidirectional LSTM neural network)
- Can capture more complex patterns
- Slightly slower
- Requires TensorFlow

### Can the model improve over time?

Yes! The system improves through:
1. **User flags**: You report incorrect predictions
2. **Admin review**: Admins validate flags
3. **Retraining**: Model is retrained with new validated data
4. **Continuous learning**: Each cycle improves accuracy

This is called "human-in-the-loop machine learning."

### How often is the model retrained?

**Recommended schedule**: Weekly or bi-weekly

**Retraining occurs when**:
- Admin manually triggers it
- Sufficient validated flags have accumulated (20+ recommended)
- New scam patterns are identified
- Model performance degrades

### What happens during retraining?

1. System loads base training dataset
2. Adds all validated flagged posts
3. Splits data 80/20 (train/test)
4. Trains new Logistic Regression model with hyperparameter tuning
5. Evaluates performance metrics
6. Saves versioned model
7. Activates new model (if successful)

The process takes 30-60 seconds depending on dataset size.

---

## Admin Questions

### How do I become an admin?

Admin access is restricted and must be granted by a system administrator:

1. **Create a Firebase account** via the Sign Up page
2. **Request admin access** from existing administrator
3. **Admin sets custom claim** (`admin: true`) in Firebase
4. **Log in again** to access admin dashboard

Contact your organization's system administrator for access.

### What can admins do that regular users can't?

Admins have access to:
- **Dashboard**: Real-time metrics and analytics
- **Flag Management**: Review and validate user-reported flags
- **Model Control**: Trigger retraining and rollback versions
- **Data Exports**: CSV and PDF reports
- **Activity Logs**: Monitor all predictions and admin actions
- **System Monitoring**: Track performance and health

### How do I review flagged posts?

1. Log in to admin dashboard
2. Scroll to "Flagged Posts" table
3. For each flag:
   - Read the job description
   - Check model prediction and confidence
   - Research to verify if fake or real
   - Click "Mark Fake", "Mark Real", or "Dismiss"
4. Validated flags will be used in next retraining

See [Admin Panel Guide](ADMIN_GUIDE.md) for detailed instructions.

### How do I retrain the model?

1. Ensure you have validated flags (20+ recommended)
2. Click **Retrain Model** button
3. Wait for "succeeded" status
4. Check `/model-info` endpoint for new metrics
5. Monitor predictions for improvements

If retraining fails, check server logs and ensure `fake_job_postings.csv` exists.

### Can I rollback to a previous model?

Yes!

1. Click "Select version" dropdown
2. Choose previous version from list
3. Click **Rollback** button
4. Model reverts immediately

Use rollback if new model performs worse than previous version.

---

## Troubleshooting

### "Rate limit exceeded" error

**Cause**: More than 10 predictions in 60 seconds

**Solution**:
- Wait 60 seconds before trying again
- If you need bulk analysis, contact admin about API access

### Results seem inaccurate

**Possible reasons**:
1. **New scam pattern** not in training data
2. **Partial description** provided
3. **Edge case** the model hasn't seen
4. **Model needs retraining** with recent data

**What to do**:
- Use the Flag feature to report it
- Verify through other sources
- Trust your judgment
- Help improve the system by reporting

### Page not loading

**Solutions**:
1. Check internet connection
2. Refresh the page (Ctrl+R)
3. Clear browser cache (Ctrl+Shift+Delete)
4. Try a different browser
5. Check if backend server is running

### Prediction taking too long

**Normal**: 20-80ms  
**Slow**: 100-500ms  
**Very slow**: >500ms

**Solutions**:
- Refresh and try again
- Check network connection
- Try shorter job description
- Contact admin if persistent (server may be overloaded)

### Can't log in to admin dashboard

See troubleshooting in [Admin Panel Guide](ADMIN_GUIDE.md), common issues:
- Wrong email/password
- Account doesn't have admin claim
- Firebase authentication issue

---

## Integration & API

### Can I integrate this into my website?

Yes! The system provides a REST API. Contact the administrator for:
- API documentation
- Authentication credentials
- Rate limits for your use case
- Integration support

### Is there an API for programmatic access?

Yes! The backend exposes RESTful endpoints. See [API Documentation](API.md) for:
- Endpoint specifications
- Request/response formats
- Authentication requirements
- Rate limits
- Code examples

### Can I use this commercially?

Licensing depends on your deployment. Contact the system owner for:
- Commercial licensing terms
- Usage limits
- Support agreements
- Custom development

### Can I self-host this?

Yes! The system is designed to be self-hosted. See [README.md](../README.md) for:
- Setup instructions
- Dependencies
- Configuration
- Deployment guide

---

## Model Performance

### Why does the model make mistakes on obvious scams?

Possible reasons:
1. **New scam pattern** not in training data
2. **Well-written scam** mimicking legitimate jobs
3. **Model hasn't been retrained recently** with new examples
4. **Insufficient features** - the model only sees text patterns

**Remember**: No AI is perfect. Use as one tool among many.

### Why does it flag legitimate jobs as fake?

**False positives** can occur when:
1. Legitimate jobs use **unusual wording** similar to scams
2. **Startups** with unconventional offerings
3. **Cryptocurrency/remote** jobs (often targeted by scammers)
4. **High-paying positions** with low requirements (could be real but rare)

Always research companies before applying!

### How can I help improve accuracy?

1. **Flag incorrect predictions** with details
2. **Provide context** in flag comments
3. **Be accurate** in your own research
4. **Suggest improvements** to admin team
5. **Report new scam patterns** you encounter

---

## Data & Privacy

### Can I request my data be deleted?

Since no personal accounts exist and predictions are anonymous, there's no personal data to delete. However:
- Prediction logs auto-delete after 90 days
- Flagged content can be removed by admins
- IP hashes cannot be linked back to you

### Is this GDPR compliant?

The system is designed with privacy in mind:
- No personal data collection without consent
- IP addresses are hashed
- Data retention policies (90 days for logs)
- Right to erasure (for flagged content)

Consult with legal counsel for your specific deployment and jurisdiction.

### Who has access to the data?

- **Public users**: No access to data (only their own prediction results)
- **Admins**: Access to aggregated metrics, flagged posts, activity logs
- **System admins**: Full database access
- **Third parties**: None

---

## Support & Contact

### How do I report a bug?

1. Document the issue:
   - What you were trying to do
   - What happened instead
   - Steps to reproduce
   - Browser and OS
   - Screenshots if applicable

2. Contact:
   - Email: support@example.com (update with your support email)
   - Include "BUG:" in subject line

### How do I suggest a feature?

We welcome suggestions!

1. Describe the feature clearly
2. Explain the use case
3. Estimate priority (nice-to-have vs critical)
4. Send to: features@example.com (update with your email)

### Where can I learn more?

- **User Manual**: [USER_MANUAL.md](USER_MANUAL.md)
- **Admin Guide**: [ADMIN_GUIDE.md](ADMIN_GUIDE.md)
- **API Docs**: [API.md](API.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Database Schema**: [DATABASE.md](DATABASE.md)

### How do I get support?

**For users**:
- Check this FAQ
- Review User Manual
- Email: support@example.com

**For admins**:
- Check Admin Panel Guide
- Review Troubleshooting Guide
- Email: admin-support@example.com

**Response time**: 24-48 hours for general inquiries, 2-4 hours for urgent admin issues during business hours.

---

## Best Practices

### For Job Seekers

✓ **Do**:
- Use the detector as ONE verification tool
- Research companies independently
- Check multiple job boards
- Look for company reviews on Glassdoor
- Verify contact information
- Trust your instincts
- Report suspicious jobs

✗ **Don't**:
- Rely solely on the prediction
- Share personal information without verification
- Pay fees for job applications
- Rush into applications
- Ignore red flags

### For Admins

✓ **Do**:
- Review flags promptly
- Research thoroughly before validating
- Retrain model regularly
- Monitor system performance
- Export data for backups
- Document your decisions
- Secure your credentials

✗ **Don't**:
- Validate without verification
- Ignore user flags
- Let flags pile up
- Skip retraining
- Share admin access
- Leave dashboard unattended

---

## Version & Updates

### What version is currently running?

Check the footer of the web interface or visit:
```
http://localhost:8000/model-info
```

This shows the current model version and training date.

### How do I know when updates are available?

- System administrators receive update notifications
- Check the project repository for releases
- Subscribe to update announcements (if available)

### Can I upgrade without losing data?

Yes! Database schema is versioned and migration-safe. Always:
1. Backup database before upgrading
2. Test in development environment first
3. Follow upgrade guide in README
4. Export critical data

---

## Glossary

**API**: Application Programming Interface - allows programmatic access  
**Confidence**: Probability score indicating model certainty  
**False Positive**: Legitimate job incorrectly flagged as fake  
**False Negative**: Fake job incorrectly marked as real  
**Flag**: User report of suspicious or incorrect prediction  
**Latency**: Time taken to process prediction (milliseconds)  
**Model**: Machine learning algorithm that makes predictions  
**Precision**: Percentage of fake predictions that are actually fake  
**Recall**: Percentage of actual fakes that were caught  
**Retraining**: Updating the model with new data  
**TF-IDF**: Text feature extraction method  
**Validation**: Admin confirmation of flag accuracy  
**Version**: Timestamped snapshot of model  

---

**Document Version**: 1.0  
**Last Updated**: January 4, 2026  
**For More Information**: See other documentation files
