# Web App Updates for Dual Pinecone Indexes

## Summary
Updated the web application to work with the new dual-index Pinecone setup and new embedding metadata structure.

## Changes Made

### 1. app.py - Main Web Application

**Added Supabase Integration:**
- Imported `supabase` client to fetch full document text
- Added `self.supabase` to `SearchSystem` class
- Initialized Supabase connection in `initialize()` method
- Created `get_document_text()` method to fetch full text from Supabase using cite_id

**Updated Search Functionality:**
- Changed metadata field from `section_name` to `page_title` (matches new embedding structure)
- Fetch full document text from Supabase instead of storing it in Pinecone metadata
- Updated statute source labels from "Oklahoma Statutes - Title 10" to dynamic "Oklahoma Statutes - Title {X}"
- Improved source labeling to show Article/Section for Constitution and Title/Section for Statutes

**Key Changes:**
- Line 26: Added Supabase import
- Lines 70, 85-91: Added Supabase client initialization
- Lines 112-125: Added `get_document_text()` method
- Lines 148-210: Updated search results to use correct metadata fields and fetch text from Supabase

### 2. rag_search.py - RAG Question Answering

**Added Supabase Integration:**
- Imported `supabase` client and config variables
- Added `self.supabase` to `ConstitutionRAG` class
- Initialized Supabase connection in `initialize()` method
- Created `get_document_text()` method to fetch full text

**Updated Search Results Processing:**
- Changed metadata field from `section_name` to `page_title`
- Fetch full document text from Supabase instead of Pinecone metadata

**Key Changes:**
- Lines 10, 15-21: Added Supabase imports and config
- Lines 27, 42-48: Added Supabase client initialization
- Lines 67-76: Added `get_document_text()` method
- Lines 99-107: Updated results to use correct metadata fields

## Metadata Structure

### Old Structure (Expected)
```python
{
    'cite_id': 'xxx',
    'section_name': 'xxx',  # Changed to page_title
    'text': '...',           # Removed - now fetched from Supabase
    'article_number': 'xxx',
    'section_number': 'xxx',
    'title_number': 'xxx'
}
```

### New Structure (Actual)
```python
{
    'cite_id': 'xxx',
    'document_type': 'constitution' or 'statute',
    'page_title': 'xxx',       # Renamed from section_name
    'article_number': 'xxx',   # Constitution only
    'section_number': 'xxx',
    'title_number': 'xxx'      # Statutes only
}
# Full text stored in Supabase, not in Pinecone metadata
```

## Why These Changes?

1. **Efficiency**: Storing full text in Pinecone metadata bloats the index and increases costs. We now store only the cite_id and fetch full text from Supabase when needed.

2. **Accuracy**: The metadata field names now match what we actually stored during embedding generation.

3. **Coverage**: Updated statute labels to reflect all 85 titles instead of just "Title 10".

4. **Better UX**: Improved source labeling (e.g., "Oklahoma Constitution - Article II, Section 7" or "Oklahoma Statutes - Title 43, Section 101")

## Testing Recommendations

1. **Test Search Functionality:**
   ```bash
   python app.py
   ```
   - Try searching for constitution topics
   - Try searching for statute topics
   - Try searching both (source='both')

2. **Test RAG System:**
   ```bash
   python rag_search.py
   ```
   - Test with sample questions about the Oklahoma Constitution

3. **Verify Supabase Connection:**
   - Ensure SUPABASE_URL and SUPABASE_KEY are set as environment variables
   - Check that documents are being fetched correctly

## Deployment Notes

When deploying to Render, ensure these environment variables are set:
- `PINECONE_API_KEY`
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `PRODUCTION=true` or `RENDER=true`

## Next Steps

1. Test the updated app locally
2. Commit changes to git
3. Push to GitHub
4. Render will auto-deploy the changes
5. Test the production deployment
