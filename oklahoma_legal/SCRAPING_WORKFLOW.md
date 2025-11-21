# Complete Oklahoma Legal Database Scraping Workflow

## Overview
Scrape and process the complete Oklahoma legal system:
- **Oklahoma Constitution** (~200 sections)
- **Oklahoma Statutes** - Titles 10-85 (~10,000+ sections)

## Prerequisites
- IP whitelisted by OSCN (IP: 24.117.162.107)
- Python environment set up
- API keys configured (OpenAI, Pinecone, Supabase)

---

## Phase 1: Collect URLs

### Constitution URLs
```bash
python url_collector.py
# Choose option 1: Collect Oklahoma Constitution
# Output: constitution_urls.json
```

### Statute URLs (All Titles)
```bash
python url_collector.py
# Choose option 2: Collect all statute titles (1-85)
# Time: ~15 minutes with 10-second delay
# Output: oklahoma_statute_urls.json
```

### Statute URLs (Specific Range)
```bash
python url_collector.py
# Choose option 3: Collect specific title range
# Enter: start=10, end=20
# Output: titles_10_to_20_urls.json
```

---

## Phase 2: Download HTML Files

### Download Constitution
```bash
python slow_downloader.py constitution_urls.json constitution
# Output: statute_html/constitution/*.html + *.meta.json
# Time: ~30 minutes (200 sections × 10 seconds)
```

### Download All Statutes
```bash
python slow_downloader.py oklahoma_statute_urls.json all
# Output: statute_html/title_XX/*.html + *.meta.json
# Time: ~30 hours (10,000 sections × 10 seconds)
```

### Download Specific Titles
```bash
python slow_downloader.py titles_10_to_20_urls.json 10-20
# Output: statute_html/title_10/, title_11/, ..., title_20/
```

---

## Phase 3: Process to Databases

### Process Constitution
```bash
python process_statutes.py --constitution
# → Uploads to Supabase (statutes table, type='constitution')
# → Creates embeddings → Pinecone (oklahoma-constitution index)
```

### Process All Statutes
```bash
python process_statutes.py --all-titles
# → Uploads to Supabase (statutes table, type='statute')
# → Creates embeddings → Pinecone (oklahoma-statutes index)
```

### Process Specific Title
```bash
python process_statutes.py --title 10
# → Process only Title 10
```

---

## Phase 4: Archive Raw Data

### Archive Everything
```bash
python archive_raw_data.py --all
# Creates:
# - archives/raw_data_constitution_TIMESTAMP.zip
# - archives/raw_data_all_titles_TIMESTAMP.zip
# - Manifest files with MD5 checksums
```

### Archive Specific Title
```bash
python archive_raw_data.py --title 10
# Creates:
# - archives/raw_data_title_10_TIMESTAMP.zip
```

---

## Complete Fresh Start Workflow

When starting from scratch with IP whitelisted:

```bash
# 1. Clear old data (with backup)
python clear_data.py --confirm

# 2. Collect all URLs
python url_collector.py  # Option 1 - Constitution
python url_collector.py  # Option 2 - All statutes

# 3. Download Constitution
python slow_downloader.py constitution_urls.json constitution

# 4. Download All Statutes (overnight)
python slow_downloader.py oklahoma_statute_urls.json all

# 5. Process Constitution
python process_statutes.py --constitution

# 6. Process All Statutes
python process_statutes.py --all-titles

# 7. Archive Everything
python archive_raw_data.py --all

# 8. Deploy updated web app
git add .
git commit -m "Complete Oklahoma legal database"
git push origin main
```

---

## Directory Structure After Scraping

```
statute_html/
├── constitution/
│   ├── cite_63230.html
│   ├── cite_63230.meta.json
│   └── ... (~200 files)
│
├── title_10/
│   ├── cite_103841.html
│   ├── cite_103841.meta.json
│   └── ... (~1,000 files)
│
├── title_11/
│   └── ... (~500 files)
│
└── ... (titles 12-85)

archives/
├── raw_data_constitution_TIMESTAMP.zip
├── raw_data_constitution_TIMESTAMP_manifest.json
├── raw_data_all_titles_TIMESTAMP.zip
└── raw_data_all_titles_TIMESTAMP_manifest.json
```

---

## Estimated Times & Costs

| Task | Time | Cost |
|------|------|------|
| Collect Constitution URLs | 10 seconds | Free |
| Collect All Statute URLs | 15 minutes | Free |
| Download Constitution | 30 minutes | Free |
| Download All Statutes | 30 hours | Free |
| Process Constitution | 5 minutes | ~$0.02 |
| Process All Statutes | 2 hours | ~$1.50 |
| **Total** | **~32 hours** | **~$1.52** |

**Note:** Downloading is the time bottleneck (10-second delays). Processing is fast and cheap.

---

## Resume Capability

All scripts support resume:
- **URL Collector:** Re-run safely, skips already collected
- **Downloader:** Checks for existing files, skips downloaded
- **Processor:** Can reprocess from HTML anytime

If interrupted:
1. Check `download_progress.json` for status
2. Re-run same command - automatically resumes
3. No duplicate downloads or processing

---

## Safety Features

✅ **Respectful Delays:** 10 seconds between requests
✅ **Progress Tracking:** Resume from interruption
✅ **User-Agent:** Identifies scraper with contact email
✅ **IP Whitelist:** Approved by OSCN before scraping
✅ **Raw Data Archive:** Never need to re-scrape
✅ **Dry-Run Mode:** Test commands safely first

---

## Troubleshooting

### IP Blocked Again
- Stop all scraping immediately
- Wait 24 hours
- Contact OSCN webmaster
- Consider increasing delay (15-20 seconds)

### Download Failed
- Check internet connection
- Verify IP still whitelisted
- Check download_progress.json
- Re-run downloader (resumes automatically)

### Processing Failed
- Check API keys (OpenAI, Pinecone, Supabase)
- Verify HTML files exist
- Check error logs
- Can reprocess from HTML anytime

---

## Post-Scraping Tasks

After complete scraping:

1. **Verify Data**
   ```bash
   python verify_data.py
   # Check: File counts, database records, vector counts
   ```

2. **Update Web App**
   - Ensure app searches both Constitution and Statutes
   - Test search functionality
   - Deploy to Render

3. **Backup Archives**
   - Upload ZIP files to cloud storage
   - Keep manifest files separately
   - Document scraping date and version

4. **Monitor Usage**
   - Track API costs (OpenAI)
   - Monitor Pinecone vector count
   - Check Supabase storage

---

## Key Takeaways

**Do Once (Expensive):**
- Scrape HTML from OSCN (~32 hours)
- Requires IP whitelist

**Do Anytime (Cheap/Free):**
- Reprocess HTML to databases
- Regenerate embeddings
- Update schema
- Change processing logic

**Golden Rule:**
Raw HTML files are your single source of truth. Never delete them. Everything else can be regenerated.
