# Oklahoma Statutes Scraping - Quick Start Guide

## Overview

This toolset collects Oklahoma statutes from OSCN in a respectful, semi-automated way that works around Cloudflare protection.

## Three-Phase Process

```
Phase 1: URL Collection (15 min)
    ↓
Phase 2: HTML Download (5-8 days)
    ↓
Phase 3: Database Upload (2-4 hours)
```

---

## Phase 1: Collect URLs

**Tool:** `url_collector.py`

**What it does:** Visits OSCN title index pages and collects all statute URLs

**Run it:**
```bash
python url_collector.py
```

**Options:**
1. Collect all titles (1-85) - Takes ~15 minutes
2. Collect specific title range
3. Test with single title

**Output:** `oklahoma_statute_urls.json` (list of all statute URLs)

**Recommendation:** Start with option 3 (single title) to test before running full collection.

---

## Phase 2: Download HTML

**Tool:** `slow_downloader.py`

**What it does:** Downloads HTML for each statute with 10-second delays

**Run it:**
```bash
python slow_downloader.py
```

**Options:**
1. Download all statutes (WARNING: Takes days)
2. Download specific titles
3. Resume previous download
4. Show download statistics

**Output:** `statute_html/` directory with subdirectories for each title
- HTML files: `statute_html/title_01/cite_123456.html`
- Metadata: `statute_html/title_01/cite_123456.meta.json`
- Progress: `download_progress.json`

**Features:**
- Resume capability (safe to interrupt with Ctrl+C)
- Progress saved every 10 downloads
- Skips already-downloaded files

**Time Estimate:**
- Single title: 1-2 hours
- All statutes: 5-8 days (continuous)

**Recommendation:**
1. Test with 1-2 titles first
2. Then run full download overnight/over weekend
3. Can pause and resume at any time

---

## Phase 3: Process into Database

**Tool:** `html_processor.py`

**What it does:** Parses HTML files, generates embeddings, uploads to Pinecone

**First-time setup:**
```bash
python html_processor.py
# Choose option 4 to create the Pinecone index
```

**Run processing:**
```bash
python html_processor.py
```

**Options:**
1. Process all statutes
2. Process specific title range
3. Resume previous processing
4. Create statute index (one-time setup)
5. Show processing statistics

**Output:**
- Vectors uploaded to Pinecone `oklahoma-statutes` index
- Progress saved in `processing_progress.json`

**Features:**
- Batch processing (50 records at a time)
- Resume capability
- Progress tracking
- Automatic embedding generation

**Time Estimate:**
- Per 1000 statutes: ~15-20 minutes
- All 50,000 statutes: 2-4 hours

**Costs:**
- Embeddings: ~$50-100 (one-time)
- Pinecone: ~$70/month for storage

---

## Testing Strategy

### Test Run (Recommended First)

**Step 1:** Collect URLs for Title 1
```bash
python url_collector.py
# Choose option 3, enter "1"
```

**Step 2:** Download Title 1 HTML
```bash
python slow_downloader.py
# Choose option 2, enter "1"
```

**Step 3:** Create index (if not exists)
```bash
python html_processor.py
# Choose option 4
```

**Step 4:** Process Title 1
```bash
python html_processor.py
# Choose option 2, enter start=1, end=1
```

**Result:** You'll have Title 1 fully indexed as a test before committing to the full dataset.

---

## Full Production Run

Once you've tested with a single title:

### Week 1: Data Collection

**Monday:**
```bash
python url_collector.py
# Option 1 (all titles) - 15 minutes
```

**Monday-Friday:**
```bash
python slow_downloader.py
# Option 1 (all statutes)
# Let it run continuously
# Can interrupt evenings and resume mornings
```

### Week 2: Database Upload

**Weekend:**
```bash
python html_processor.py
# Option 1 (all statutes) - 2-4 hours
```

---

## Progress Tracking

### Check Download Progress
```bash
python slow_downloader.py
# Choose option 4 (statistics)
```

### Check Processing Progress
```bash
python html_processor.py
# Choose option 5 (statistics)
```

### Check Files
```bash
# Count HTML files
ls statute_html/title_*/*.html | wc -l

# Check specific title
ls statute_html/title_01/
```

---

## Resume After Interruption

All tools support resume:

**URL Collection:** Just re-run, it's fast enough to redo

**HTML Download:**
```bash
python slow_downloader.py
# Option 3 (resume)
```

**HTML Processing:**
```bash
python html_processor.py
# Option 3 (resume)
```

Progress files:
- `download_progress.json` - Download tracking
- `processing_progress.json` - Processing tracking

---

## Troubleshooting

### "No URLs found"
- Check internet connection
- OSCN might be down, try again later
- Check `oklahoma_statute_urls.json` was created

### "Failed to download cite_id X"
- Normal - some URLs may be invalid
- Downloader will skip and continue
- Check error message for details

### "Content too short"
- Some pages may not have much text
- Processor will skip and continue
- Check HTML file manually if concerned

### "Index does not exist"
```bash
python html_processor.py
# Choose option 4 to create index
```

### Rate limiting / Connection errors
- OSCN may be rate limiting
- Increase delay in code (change from 10 to 15 seconds)
- Wait and resume later

---

## Integration with Web App

After processing, update your web application:

### Update app.py

```python
# Change index name from constitution to statutes
index = pc.Index("oklahoma-statutes")  # Instead of "oklahoma-constitution"
```

### Update search to include both

```python
def search_oklahoma_law(query):
    # Search constitution
    const_results = pc.Index("oklahoma-constitution").query(...)

    # Search statutes
    statute_results = pc.Index("oklahoma-statutes").query(...)

    # Combine and rank results
    return combined_results
```

---

## Cost Breakdown

### One-Time Costs
- OpenAI embeddings: $50-100
- Development time: Already done!

### Ongoing Costs
- Pinecone storage: $70/month
- OpenAI API (queries): $2-10/day depending on usage

### Total to Full Legal System
- Initial setup: $50-100
- Monthly: $230-380 (Phase 1 from expansion plan)

---

## Next Steps After Completion

Once you have all statutes indexed:

1. **Test the search** - Try various legal queries
2. **Update web interface** - Add statute search alongside constitution
3. **Deploy to Render** - Push updated code
4. **Monitor usage** - Track costs and performance
5. **Phase 2** - Consider adding case law (see LEGAL_EXPANSION_PLAN.md)

---

## Files Reference

### Created by Tools
- `oklahoma_statute_urls.json` - URL list (Phase 1)
- `statute_html/` - HTML files (Phase 2)
- `download_progress.json` - Download tracking
- `processing_progress.json` - Processing tracking

### Scripts
- `url_collector.py` - Phase 1 tool
- `slow_downloader.py` - Phase 2 tool
- `html_processor.py` - Phase 3 tool

### Documentation
- `manual_scraping_guide.md` - Detailed methodology
- `SCRAPING_QUICKSTART.md` - This file
- `LEGAL_EXPANSION_PLAN.md` - Long-term roadmap

---

## Support

If you encounter issues:

1. Check the manual scraping guide for detailed explanations
2. Review error messages (most are self-explanatory)
3. Test with a single title first before full run
4. All tools support interruption and resume

---

## Legal & Ethical Notes

✅ **This is respectful scraping:**
- 10-second delays between requests
- Proper User-Agent identification
- Public legal information
- Educational purpose
- No server overload

✅ **Best practice:**
- Consider emailing OSCN first (webmaster@oscn.net)
- Ask if bulk data access available
- Explain educational purpose
- They may provide direct access

---

**Ready to start!** Begin with the test run (single title) to verify everything works.
