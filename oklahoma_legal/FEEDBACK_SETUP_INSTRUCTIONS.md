# Feedback System Setup Instructions

## Step 1: Create Database Tables in Supabase

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" in the left sidebar
4. Click "New Query"
5. Copy the entire contents of `feedback_schema.sql`
6. Paste into the SQL editor
7. Click "Run" (or press Ctrl/Cmd + Enter)

You should see success messages for:
- ✅ Created `user_feedback` table
- ✅ Created `document_performance` table
- ✅ Created indexes
- ✅ Created trigger function
- ✅ Set up Row Level Security policies

## Step 2: Verify Tables Were Created

Run this query in Supabase SQL Editor to verify:

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('user_feedback', 'document_performance');

-- Check current data (should be empty initially)
SELECT COUNT(*) as feedback_count FROM user_feedback;
SELECT COUNT(*) as performance_count FROM document_performance;
```

You should see both tables listed and counts of 0.

## Step 3: Test Locally (Optional but Recommended)

Before deploying to production, test the feedback system locally:

1. Make sure the local app is running:
   ```bash
   python app.py
   ```

2. Open http://localhost:5000 in your browser

3. Ask a question (e.g., "What are child custody laws in Oklahoma?")

4. After getting an answer, you should see thumbs up/down buttons

5. Click either button

6. You should see "Thanks for your feedback!" message

7. Check Supabase to verify the feedback was stored:
   ```sql
   SELECT * FROM user_feedback ORDER BY created_at DESC LIMIT 5;
   SELECT * FROM document_performance ORDER BY last_updated DESC LIMIT 5;
   ```

## Step 4: Deploy to Production

The code is already committed (commit f90935c). Just push to GitHub:

```bash
git push origin main
```

Render will automatically deploy the update.

## Step 5: Monitor Feedback

After deployment, you can monitor feedback in Supabase:

### View Recent Feedback
```sql
SELECT
    question,
    rating,
    answer_type,
    model_used,
    created_at
FROM user_feedback
ORDER BY created_at DESC
LIMIT 20;
```

### View Top Performing Documents
```sql
SELECT
    cite_id,
    feedback_score,
    positive_feedback,
    negative_feedback,
    total_shown
FROM document_performance
WHERE total_shown > 2  -- At least 3 ratings
ORDER BY feedback_score DESC
LIMIT 10;
```

### View Worst Performing Documents
```sql
SELECT
    cite_id,
    feedback_score,
    positive_feedback,
    negative_feedback,
    total_shown
FROM document_performance
WHERE total_shown > 2
ORDER BY feedback_score ASC
LIMIT 10;
```

### View Feedback Rate
```sql
SELECT
    COUNT(*) as total_feedback,
    SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as positive,
    SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as negative,
    ROUND(100.0 * SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as positive_percentage
FROM user_feedback;
```

## Next Steps

Once you have ~100 feedback entries, you can:

1. **Implement re-ranking** - Use feedback scores to boost/penalize documents
2. **Identify problem areas** - Find queries that consistently get negative feedback
3. **A/B testing** - Test if feedback-enhanced ranking improves results

See `FEEDBACK_SYSTEM_PLAN.md` for the full implementation roadmap.

## Troubleshooting

### Feedback not being stored
- Check browser console for errors
- Check Supabase logs
- Verify RLS policies are correct

### "Failed to submit feedback" error
- Check that Supabase credentials are set in Render environment variables
- Check Render logs for detailed error messages

### Trigger not updating document_performance
- Verify the trigger was created successfully
- Check for errors in Supabase logs
- Manually run: `SELECT * FROM document_performance;` to see if it's being updated
