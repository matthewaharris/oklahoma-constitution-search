# Production Debugging Guide - What to Do Next

## What I Just Did

I've added comprehensive diagnostic logging to help identify why the production deployment behaves differently than local. The changes have been pushed to GitHub and should trigger a Render auto-deployment.

### Changes Made:

1. **app.py** - Added debug logging to the search function:
   - Logs when each index is queried
   - Logs how many results each index returns
   - Logs the final breakdown (Constitution vs Statutes)

2. **rag_search.py** - Added debug logging to the RAG system:
   - Logs when each index is queried during question answering
   - Logs how many sources come from each index
   - Logs the final source breakdown

3. **diagnose_pinecone.py** - Created a diagnostic script:
   - Tests Pinecone API key
   - Verifies connection to both indexes
   - Shows vector counts
   - Tests query capability

4. **DIAGNOSTIC_LOGGING.md** - Comprehensive documentation

## What to Do Next

### Step 1: Wait for Render Deployment

1. Go to your Render dashboard
2. Open your web service
3. Watch for the deployment to complete (should show commit `0d5f779`)
4. Look for "Deploy live for 0d5f779" message

### Step 2: Check Render Logs Immediately After Deployment

When the app starts up, you should see initialization logs:

```
Initializing search system...
[OK] Connected to Supabase
[OK] Connected to Constitution index with 491 vectors
[OK] Connected to Statutes index with 49600 vectors
```

**⚠️ CRITICAL: If you see an error like this:**
```
[ERROR] Failed to connect to indexes: Index 'oklahoma-statutes' not found
```

**Then the problem is clear:** The production Pinecone API key doesn't have access to the statutes index.

### Step 3: Test the Production App

Open your production app and try these tests:

#### Test 1: Search Function
Search for: "child custody"

**In the Render logs, you should see:**
```
[DEBUG] Searching Constitution index for: 'child custody' (top_k=5)
[DEBUG] Constitution search returned 5 results
[DEBUG] Searching Statutes index for: 'child custody' (top_k=5)
[DEBUG] Statutes search returned 5 results
[DEBUG] Returning 5 results: 1 from Constitution, 4 from Statutes
```

#### Test 2: RAG Function
Ask: "What are child custody laws in Oklahoma?"

**In the Render logs, you should see:**
```
[DEBUG] RAG: Searching Constitution index for: 'What are child custody laws...' (top_k=3)
[DEBUG] RAG: Constitution search returned 3 results
[DEBUG] RAG: Searching Statutes index for: 'What are child custody laws...' (top_k=3)
[DEBUG] RAG: Statutes search returned 3 results
[DEBUG] RAG: Returning 3 results: 0 from Constitution, 3 from Statutes
```

## What the Logs Will Tell You

### Scenario 1: Both indexes are being searched

If you see logs showing both indexes being queried and returning results, then:
- ✅ The connection is working
- ✅ Both indexes are accessible
- ❓ The issue is with result quality or model selection

**Next steps:**
- Check which OpenAI model is being used in production
- Compare the actual responses between local and production
- Check if the sources being returned are different

### Scenario 2: Only Constitution is being searched

If you see logs showing only Constitution being queried, then:
- ❌ The Statutes index connection failed
- ❌ The `source` parameter might not be set to 'both'

**Next steps:**
- Check the initialization logs for connection errors
- Verify environment variables in Render:
  - `PINECONE_API_KEY`
  - `OPENAI_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`

### Scenario 3: Connection errors on startup

If you see errors during initialization:
```
[ERROR] Failed to connect to indexes: ...
```

Then the problem is with the Pinecone configuration.

**Next steps:**
- Verify `PINECONE_API_KEY` is set correctly in Render
- Check that the API key has access to both indexes
- Verify the indexes exist in the correct Pinecone environment

## Environment Variables to Check in Render

Go to Render Dashboard → Your Service → Environment

**Required variables:**
```
PINECONE_API_KEY=pc-...
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...
PRODUCTION=true
```

**Optional but recommended:**
```
RENDER=true
```

## Quick Diagnostic Commands

If you have access to run commands on Render (via shell or as part of deployment):

```bash
# Test Pinecone connection
python diagnose_pinecone.py

# Check environment variables are set
env | grep -E "(PINECONE|OPENAI|SUPABASE|PRODUCTION|RENDER)"
```

## Local Verification (Already Done)

I've already tested locally and confirmed:
- ✅ Both indexes are accessible (491 Constitution, 49,600 Statutes)
- ✅ Queries work on both indexes
- ✅ Results are returned from both indexes
- ✅ RAG system searches both indexes

This confirms the code is correct and the issue is environment-specific.

## Common Issues and Fixes

### Issue: "Index not found" error

**Cause:** Pinecone API key doesn't have access to that index

**Fix:**
1. Log into Pinecone console
2. Check that both indexes exist:
   - `oklahoma-constitution`
   - `oklahoma-statutes`
3. Verify the API key has access to both indexes
4. Create a new API key if needed and update Render environment

### Issue: Empty results from statutes

**Cause:** Embeddings weren't uploaded to statutes index

**Fix:**
1. Run locally: `python check_progress.py` to verify embeddings were created
2. Check Pinecone console for vector counts in both indexes
3. If statutes index is empty, re-run embedding generation

### Issue: Different OpenAI model being used

**Cause:** Production might be defaulting to gpt-3.5-turbo instead of gpt-4

**Fix:**
1. Check the RAG request to see which model is being used
2. Update the frontend to explicitly request gpt-4 if available
3. Or set a default model in the backend

## Expected Timeline

1. **Now:** Changes pushed to GitHub
2. **~5 minutes:** Render detects changes and starts deployment
3. **~10 minutes:** Deployment completes, new version is live
4. **Immediately after:** You can start seeing the debug logs
5. **After testing:** We'll know exactly what's wrong

## What to Report Back

After the deployment completes and you've tested the production app, please share:

1. **Startup logs:** What you see when the app initializes
   - Did both indexes connect successfully?
   - Any error messages?

2. **Search test logs:** What you see when searching
   - Are both indexes being queried?
   - How many results from each?

3. **RAG test logs:** What you see when asking questions
   - Are both indexes being queried?
   - How many sources from each?

4. **Any error messages** you see in the logs

This will tell us exactly what's happening and we can fix it immediately.

## My Hypothesis

Based on the symptoms (local works perfectly, production doesn't search statutes), I suspect one of:

1. **Most likely:** The Pinecone API key in production doesn't have access to the `oklahoma-statutes` index
2. **Less likely:** The statutes index doesn't exist in the production Pinecone environment
3. **Unlikely:** Network/firewall issue blocking access to specific indexes

The diagnostic logs will confirm which of these is the issue.
