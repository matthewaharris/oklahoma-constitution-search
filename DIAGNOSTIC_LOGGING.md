# Diagnostic Logging for Production Deployment Issues

## Problem Statement

The locally deployed app works perfectly and searches both Constitution and Statutes indexes, but the production deployment on Render appears to only search the Constitution or gives lower quality responses.

## Diagnostic Changes Made

### 1. Added Debug Logging to app.py

Added logging statements in the `search()` method to track:
- When each index (Constitution/Statutes) is being searched
- How many results each index returns
- Final breakdown of results by type

**Log output format:**
```
[DEBUG] Searching Constitution index for: 'query text' (top_k=5)
[DEBUG] Constitution search returned 5 results
[DEBUG] Searching Statutes index for: 'query text' (top_k=5)
[DEBUG] Statutes search returned 5 results
[DEBUG] Returning 5 results: 2 from Constitution, 3 from Statutes
```

### 2. Added Debug Logging to rag_search.py

Added similar logging to the RAG system's `search_relevant_sections()` method:

**Log output format:**
```
[DEBUG] RAG: Searching Constitution index for: 'query text' (top_k=3)
[DEBUG] RAG: Constitution search returned 3 results
[DEBUG] RAG: Searching Statutes index for: 'query text' (top_k=3)
[DEBUG] RAG: Statutes search returned 3 results
[DEBUG] RAG: Returning 3 results: 1 from Constitution, 2 from Statutes
```

### 3. Created Pinecone Diagnostic Script

Created `diagnose_pinecone.py` to test:
- Pinecone API key configuration
- Connection to both indexes
- Vector counts in each index
- Ability to create embeddings
- Ability to query both indexes

## How to Use These Diagnostics

### On Render (Production)

1. **View Render Logs:**
   - Go to Render dashboard
   - Open your web service
   - Click "Logs" tab
   - Look for `[DEBUG]` statements when making search or RAG requests

2. **Run Diagnostic Script on Render:**
   - SSH into Render instance (if available) or add to deployment
   - Run: `python diagnose_pinecone.py`
   - Check output for connection issues

3. **Test Endpoints:**
   ```bash
   # Test search endpoint
   curl -X POST https://your-app.onrender.com/search \
     -H "Content-Type: application/json" \
     -d '{"query": "voting rights", "source": "both", "top_k": 5}'

   # Test RAG endpoint
   curl -X POST https://your-app.onrender.com/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "What are child custody laws in Oklahoma?", "num_sources": 3}'
   ```

### Locally

1. **Run diagnostic script:**
   ```bash
   python diagnose_pinecone.py
   ```

2. **Start app with debug output:**
   ```bash
   python app.py
   ```
   Then make requests and watch the console for `[DEBUG]` statements.

## Expected Behavior

### Successful Dual-Index Search

When searching with `source='both'`, you should see:
1. Both indexes being queried (2 debug messages for searching)
2. Results from both indexes (2 debug messages for results returned)
3. Combined results (1 debug message showing split between Constitution and Statutes)

### Example Good Output
```
[DEBUG] Searching Constitution index for: 'child custody' (top_k=5)
[DEBUG] Constitution search returned 5 results
[DEBUG] Searching Statutes index for: 'child custody' (top_k=5)
[DEBUG] Statutes search returned 5 results
[DEBUG] Returning 5 results: 1 from Constitution, 4 from Statutes
```

### Example Problem Output
```
[DEBUG] Searching Constitution index for: 'child custody' (top_k=5)
[DEBUG] Constitution search returned 5 results
[ERROR] Failed to connect to indexes: Index 'oklahoma-statutes' not found
[DEBUG] Returning 5 results: 5 from Constitution, 0 from Statutes
```

## What to Check in Production

### 1. Environment Variables
Verify these are set in Render dashboard:
- `PINECONE_API_KEY` - Should be set and valid
- `OPENAI_API_KEY` - Should be set and valid
- `SUPABASE_URL` - Should be set
- `SUPABASE_KEY` - Should be set
- `PRODUCTION=true` or `RENDER=true` - Should be set to trigger production config

### 2. Pinecone Index Access
- Verify API key has access to **both** indexes:
  - `oklahoma-constitution`
  - `oklahoma-statutes`
- Check if indexes exist in the same Pinecone project/environment
- Verify index names are spelled correctly (case-sensitive)

### 3. Connection Errors
Look for these error patterns in logs:
- `[ERROR] Failed to connect to indexes`
- `Index 'oklahoma-statutes' not found`
- `Unauthorized` or `403 Forbidden`
- `Connection timeout`

### 4. Empty Results
If logs show searches succeeding but 0 results:
- Check vector counts: `describe_index_stats()`
- Verify embeddings were uploaded to correct index
- Check namespace usage (should be default namespace: `''`)

## Troubleshooting Steps

### Problem: Statutes index not being searched

**Symptoms:**
- Logs show only Constitution index being queried
- Results show "0 from Statutes"

**Possible causes:**
1. `source` parameter not being passed correctly (should be 'both' or 'statutes')
2. Statutes index connection failed during initialization
3. API key doesn't have access to statutes index

**Fix:**
1. Check initialization logs for connection errors
2. Run `diagnose_pinecone.py` to verify both indexes are accessible
3. Verify environment variables are set correctly

### Problem: Low quality responses in production

**Symptoms:**
- Responses seem less comprehensive than local
- Missing relevant statute information

**Possible causes:**
1. Using different OpenAI model (gpt-3.5-turbo instead of gpt-4)
2. Token limits causing truncation
3. Statutes not being included in context

**Fix:**
1. Check which model is being used in logs
2. Verify `model` parameter in /ask requests
3. Check RAG debug logs to see which sources are being retrieved

### Problem: Context length errors

**Symptoms:**
- Error: "maximum context length is 8192 tokens"
- RAG returns error message

**Status:**
Already fixed in latest code with text truncation (1,500 chars per source) and reduced max_tokens (500).

## Files Modified

- `app.py` - Lines 156-162, 190-196, 225-228
- `rag_search.py` - Lines 106-112, 139-145, 174-177
- `diagnose_pinecone.py` - New file

## Next Steps After Logging Analysis

Once you can see the logs from production:

1. **If both indexes are being searched:**
   - Problem is likely with result quality or model selection
   - Check which OpenAI model is being used
   - Compare token usage between local and production

2. **If only Constitution is being searched:**
   - Problem is with Statutes index connection
   - Check environment variables
   - Verify API key permissions
   - Check index name spelling

3. **If connection errors appear:**
   - Problem is with Pinecone authentication or network
   - Verify PINECONE_API_KEY is correctly set
   - Check if Render IP needs whitelisting
   - Verify index exists in correct Pinecone environment
