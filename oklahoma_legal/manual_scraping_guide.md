# Manual Oklahoma Statutes Collection Guide

## Problem
OSCN website blocks automated scraping. We need a respectful, semi-manual approach.

## Solution Overview
1. **Phase 1:** Manually collect all statute URLs
2. **Phase 2:** Slowly download HTML files (with delays)
3. **Phase 3:** Process HTML files offline into database

---

## Phase 1: URL Collection (Manual - 2-4 hours)

### Goal
Get a list of ALL statute URLs (Titles 1-85, all sections)

### Option A: Browser Extension Approach (Recommended)

**What we'll build:**
- Browser extension that captures URLs as you browse
- Click through OSCN, it records every statute URL
- Export to JSON when done

**Steps:**
1. Install URL capture extension
2. Browse OSCN title pages
3. Let extension collect URLs automatically
4. Export complete URL list

### Option B: Manual List Building

**Navigate OSCN structure:**
```
https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKST{Title_Number}&level=1

Examples:
Title 1:  https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKST1&level=1
Title 2:  https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKST2&level=1
...
Title 85: https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKST85&level=1
```

**For each title:**
1. Open title index page
2. Copy all section links
3. Save to text file
4. Move to next title

### Option C: Semi-Automated URL Discovery

**Use a slow, respectful crawler:**
- Start from title index pages
- Follow links with 5-10 second delays
- Only collect URLs (don't download content yet)
- Save URL list to file

---

## Phase 2: HTML Download (Automated with Manual Oversight - 8-24 hours)

### Goal
Download HTML for every statute URL, slowly and respectfully

### Download Strategy

**Timing:**
- 1 request per 5-10 seconds (respectful rate)
- Run overnight or over several days
- Pause if rate limited
- Resume capability

**Storage:**
- Save each page as HTML file
- Filename: `title_{title}_section_{section}.html`
- Organize by title folders
- Keep metadata (URL, download time)

### Tools We'll Build

1. **Slow Downloader** - Downloads with delays
2. **Progress Tracker** - Resume interrupted downloads
3. **Error Handler** - Retry failed downloads
4. **HTML Validator** - Ensure complete downloads

---

## Phase 3: Offline Processing (Automated - 2-4 hours)

### Goal
Parse all saved HTML files and load into database

### Process
1. Read HTML files from disk
2. Parse statute content
3. Extract metadata
4. Generate embeddings
5. Upload to Pinecone
6. Store in Supabase

**This is what we already know how to do!**

---

## OSCN URL Structure

### Understanding OSCN URLs

**Title Index:**
```
https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKST{TITLE}&level=1
```

**Individual Statute:**
```
https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={CITE_ID}
```

**Examples:**
- Title 1: `STOKST1`
- Title 68: `STOKST68`
- Section cite ID: `440462` (unique identifier)

### Mapping Structure

**You need to map:**
```
Title Number → Title ID → Section List → Cite IDs
```

---

## Estimated Scope

### Oklahoma Statutes Count

| Category | Estimated Count |
|----------|----------------|
| Total Titles | 85 |
| Sections per Title (avg) | 500-1000 |
| **Total Sections** | **~50,000-70,000** |
| Download time (10 sec/page) | 5-8 days (continuous) |
| Storage (HTML files) | ~2-5 GB |

---

## Respectful Scraping Principles

### What to DO:
✅ Add delays (5-10 seconds minimum)
✅ Identify yourself in User-Agent
✅ Honor robots.txt
✅ Only download during off-peak hours
✅ Cache/store locally (don't re-download)
✅ Respect any 429/503 errors (back off)

### What NOT to do:
❌ Parallel/concurrent requests
❌ Rapid-fire requests
❌ Ignore rate limits
❌ Fake User-Agent
❌ Bypass CAPTCHA programmatically
❌ Overload their servers

---

## Alternative: Check for Official Bulk Access

### Before Manual Scraping, Try:

1. **Contact OSCN Directly**
   - Email: webmaster@oscn.net
   - Ask if bulk data access available
   - Explain educational/public service purpose
   - They might provide data dump

2. **Check Oklahoma Legislature**
   - http://www.oklegislature.gov/
   - May have bulk downloads
   - Often more API-friendly

3. **Public Records Request**
   - Oklahoma Open Records Act
   - Request statute database export
   - May take weeks but could be comprehensive

---

## Next Steps (Immediate)

Choose your approach:

### Path A: Browser-Assisted Manual (Fastest to start)
1. Install URL capture tool
2. Browse OSCN manually
3. Export URL list
4. Run slow downloader overnight

### Path B: Semi-Automated (More technical)
1. Build URL discovery crawler
2. Run with 10-second delays
3. Collect all URLs (1-2 days)
4. Download HTML (5-8 days)

### Path C: Request Official Access (Best long-term)
1. Email OSCN
2. While waiting, do Path A or B
3. Use official data if provided

---

## Legal/Ethical Considerations

✅ **Public information** - Statutes are public domain
✅ **Educational purpose** - Building public legal tool
✅ **Respectful** - Not overloading servers
✅ **Proper attribution** - Credit OSCN as source

⚠️ **Terms of Service** - Review OSCN ToS
⚠️ **Rate limiting** - Respect technical limits
⚠️ **Server load** - Be considerate

---

## Tools We've Built

All tools are now complete and ready to use:

1. **`url_collector.py`** - Collect statute URLs from OSCN
   - Respectful 10-second delays
   - Saves to `oklahoma_statute_urls.json`
   - Options: all titles, specific range, or single title test
   - Estimated time: ~15 minutes for all 85 titles

2. **`slow_downloader.py`** - Download HTML files with resume capability
   - 10-second delay between downloads
   - Saves HTML + metadata to `statute_html/` directory
   - Organized by title subdirectories
   - Resume capability via progress tracking
   - Estimated time: 5-8 days for all ~50,000 sections

3. **`html_processor.py`** - Parse HTML and upload to databases
   - Parses statute content from HTML files
   - Generates OpenAI embeddings
   - Uploads to Pinecone vector database
   - Batch processing with resume capability
   - Estimated time: 2-4 hours for all files

---

## Complete Workflow

**Step 1: Collect URLs (15 minutes)**
```bash
python url_collector.py
# Choose option 1 to collect all titles
# Or option 3 to test with a single title first
```

**Step 2: Download HTML (5-8 days, can run in background)**
```bash
python slow_downloader.py
# Choose option 1 to download all
# Or option 2 to download specific titles
# Can interrupt and resume at any time
```

**Step 3: Create Pinecone Index (one-time setup)**
```bash
python html_processor.py
# Choose option 4 to create the statute index
```

**Step 4: Process HTML into Database (2-4 hours)**
```bash
python html_processor.py
# Choose option 1 to process all files
# Or option 3 to resume if interrupted
```

**Step 5: Update Web App**
- Modify `app.py` to search "oklahoma-statutes" index instead of "oklahoma-constitution"
- Deploy updated application to Render

---

Ready to start collecting Oklahoma statutes!
