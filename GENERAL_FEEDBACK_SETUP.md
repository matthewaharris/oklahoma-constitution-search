# General Feedback System Setup Instructions

## Overview

The general feedback system allows users to submit feature requests, bug reports, general feedback, and improvement suggestions. This is separate from the thumbs up/down feedback on specific answers.

## What Was Implemented

### 1. Database Schema (`general_feedback_schema.sql`)

Created a new table `general_feedback` with:
- `feedback_type`: feature_request, bug_report, general_feedback, or improvement
- `subject`: Brief description (max 200 chars)
- `message`: Detailed feedback message
- `email`: Optional email for follow-up
- `user_agent`: Browser/device information
- `session_id`: Anonymous session tracking
- Row Level Security (RLS) policies for anonymous submissions

### 2. Frontend UI (`templates/index.html`)

Added:
- **Feedback Link** in footer: "💡 Share Feedback or Request a Feature"
- **Modal Dialog** with form fields:
  - Feedback type dropdown
  - Subject input
  - Message textarea
  - Optional email field
- **Modern Design**: Matches the dark theme with glassmorphism effects
- **User Experience**:
  - Form validation
  - Loading states
  - Success message
  - Auto-close after submission
  - Escape key and click-outside to close

### 3. Backend API (`app.py`)

Added `/general-feedback` endpoint with:
- Rate limiting (10 per minute)
- Input validation and sanitization
- CORS support
- Supabase integration
- Error handling and logging

## Setup Instructions

### Step 1: Create Database Table in Supabase

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" in the left sidebar
4. Click "New Query"
5. Copy the entire contents of `general_feedback_schema.sql`
6. Paste into the SQL editor
7. Click "Run" (or press Ctrl/Cmd + Enter)

You should see success messages for:
- ✅ Created `general_feedback` table
- ✅ Created indexes
- ✅ Set up Row Level Security policies

### Step 2: Verify Table Was Created

Run this query in Supabase SQL Editor:

```sql
-- Check table exists
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name = 'general_feedback';

-- Check current data (should be empty initially)
SELECT COUNT(*) as feedback_count FROM general_feedback;
```

You should see the table listed and a count of 0.

### Step 3: Test Locally

The feedback system is already implemented in the code. To test:

1. Make sure the app is running:
   ```bash
   python app.py
   ```

2. Open http://localhost:5000 in your browser

3. Scroll to the footer and click "💡 Share Feedback or Request a Feature"

4. Fill out the form:
   - Select feedback type (e.g., "Feature Request")
   - Enter a subject (e.g., "Add search filters")
   - Write your message
   - Optionally add an email
   - Click "Submit Feedback"

5. You should see a success message and the modal will close

6. Check Supabase to verify the feedback was stored:
   ```sql
   SELECT * FROM general_feedback ORDER BY created_at DESC LIMIT 5;
   ```

### Step 4: Deploy to Production

The code is already committed. Just push to GitHub:

```bash
git add .
git commit -m "Add general feedback feature with modal UI"
git push origin main
```

Render will automatically deploy the update.

## Monitoring Feedback

After deployment, you can monitor feedback in Supabase:

### View Recent Feedback
```sql
SELECT
    feedback_type,
    subject,
    message,
    email,
    created_at
FROM general_feedback
ORDER BY created_at DESC
LIMIT 20;
```

### View Feedback by Type
```sql
SELECT
    feedback_type,
    COUNT(*) as count
FROM general_feedback
GROUP BY feedback_type
ORDER BY count DESC;
```

### View Feedback with Contact Info
```sql
SELECT
    feedback_type,
    subject,
    message,
    email,
    created_at
FROM general_feedback
WHERE email IS NOT NULL
ORDER BY created_at DESC;
```

### View Feature Requests Only
```sql
SELECT
    subject,
    message,
    email,
    created_at
FROM general_feedback
WHERE feedback_type = 'feature_request'
ORDER BY created_at DESC;
```

## Features

### User Experience
- **Easy Access**: Feedback link always visible in footer
- **Professional Modal**: Clean, modern design matching the app theme
- **Form Validation**: All required fields validated before submission
- **Loading States**: Button shows "Submitting..." during submission
- **Success Feedback**: Clear success message after submission
- **Auto-Close**: Modal closes automatically 2 seconds after success
- **Keyboard Support**: ESC key closes modal
- **Click Outside**: Clicking outside modal closes it

### Security
- **Rate Limiting**: 10 submissions per minute per IP
- **Input Sanitization**: All inputs sanitized to prevent XSS/injection
- **Field Length Limits**:
  - Subject: 200 chars
  - Message: 2000 chars
  - Email: 100 chars
- **Anonymous Submissions**: No login required, session-based tracking
- **RLS Policies**: Proper Supabase Row Level Security

### Privacy
- **Optional Email**: Users can submit anonymously
- **Session Tracking**: Anonymous session IDs for duplicate detection
- **User Agent**: Captured for debugging (browser/device info)

## Troubleshooting

### Feedback not being stored
- Check browser console for errors (F12 → Console tab)
- Check Supabase logs in the dashboard
- Verify RLS policies are correct (check `general_feedback_schema.sql`)

### "Failed to submit feedback" error
- Check that Supabase credentials are set in environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
- Check Render logs for detailed error messages
- Verify the `general_feedback` table exists in Supabase

### Modal not opening
- Check browser console for JavaScript errors
- Verify the modal HTML was added to `templates/index.html`
- Check that the feedback link onclick handler is present

### Rate limit errors
- Default limit is 10 per minute per IP
- Wait 1 minute and try again
- For testing, you can temporarily increase the limit in `app.py`

## Next Steps

Once you have feedback submissions, you can:

1. **Review regularly** - Check Supabase weekly for new submissions
2. **Prioritize features** - Count most-requested features
3. **Respond to bugs** - Use email field to follow up on critical bugs
4. **Track trends** - Analyze feedback types over time
5. **Build roadmap** - Use feature requests to guide development

## Files Modified

- `general_feedback_schema.sql` - Database schema (NEW)
- `templates/index.html` - Added modal UI and JavaScript
- `app.py` - Added `/general-feedback` endpoint
- `GENERAL_FEEDBACK_SETUP.md` - This documentation (NEW)

## Related Files

- `feedback_schema.sql` - Thumbs up/down feedback for answers
- `FEEDBACK_SYSTEM_PLAN.md` - Overall feedback system roadmap
- `FEEDBACK_SETUP_INSTRUCTIONS.md` - Setup for answer feedback
