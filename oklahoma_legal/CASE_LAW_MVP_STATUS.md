# Oklahoma Case Law MVP - Implementation Status

## Overview
Adding Oklahoma case law and AG opinions to the legal research platform (MVP: 2020-2025).

---

## ✅ Completed

### 1. Database Schema (`case_law_schema.sql`)
- **Tables Created:**
  - `oklahoma_cases` - Comprehensive case metadata and full text
  - `attorney_general_opinions` - AG opinion metadata and full text

- **Features:**
  - Full-text search indexes
  - Row Level Security (RLS) policies
  - Proper grants for anon/service_role
  - Optimized indexes for querying by date, court, citation

- **Next Step:** Run this SQL in Supabase SQL Editor

### 2. Discovery Crawler (`scrapers/case_law_discoverer.py`)
- **Purpose:** Find all CiteIDs for cases from 2020-2025
- **Courts Covered:**
  - Oklahoma Supreme Court
  - Court of Criminal Appeals
  - Court of Civil Appeals

- **Features:**
  - Respectful rate limiting (2 seconds between requests)
  - Saves discovered CiteIDs to JSON for later scraping
  - Progress tracking
  - Error handling

- **Next Step:** Run discovery crawler to find all CiteIDs

---

## 📋 TODO - Next Steps

### Step 1: Create Database Tables ⏳
**You need to do this:**
1. Open Supabase SQL Editor
2. Run `case_law_schema.sql`
3. Verify tables were created

```sql
-- Verification query
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('oklahoma_cases', 'attorney_general_opinions');
```

### Step 2: Run Discovery Crawler ⏳
**Discover all case CiteIDs:**
```bash
cd scrapers
python case_law_discoverer.py
```

**Expected Output:**
- `discovered_cases.json` with ~15,000-25,000 CiteIDs
- Runtime: ~30-60 minutes (with rate limiting)

### Step 3: Build Case Parser (In Progress)
**Need to create:** `scrapers/case_law_scraper.py`
- Parse HTML from `DeliverDocument.asp?CiteID=XXXXX`
- Extract metadata (citation, parties, judges, etc.)
- Extract opinion text
- Store in Supabase

### Step 4: Build AG Opinion Discoverer & Scraper
**Need to create:**
- `scrapers/ag_opinion_discoverer.py`
- `scrapers/ag_opinion_scraper.py`

### Step 5: Generate Embeddings
**Need to create:** `scrapers/case_law_embedder.py`
- Chunk long opinions intelligently
- Generate OpenAI embeddings
- Upload to Pinecone

### Step 6: Integrate Search
**Need to update:** `app.py`
- Add case law search endpoint
- Cross-reference citations
- Update UI

---

## 📊 MVP Scope Estimates

### Data Volume (2020-2025)
| Court | Estimated Cases |
|-------|----------------|
| Supreme Court | 500-1,000 |
| Criminal Appeals | 8,000-12,000 |
| Civil Appeals | 5,000-8,000 |
| **Total Cases** | **13,500-21,000** |
| **AG Opinions** | **250-300** |

### Costs
- **Embedding Generation:** ~$5-7
- **Pinecone Storage:** ~$10/month (free tier may suffice)
- **Supabase Storage:** Free tier sufficient

### Timeline
- **Discovery:** 1 hour
- **Scraping:** 12-24 hours (automated)
- **Embedding:** 2-4 hours
- **Integration:** 1-2 days (dev work)
- **Total:** ~1 week

---

## 🏗️ File Structure

```
stait/
├── case_law_schema.sql                 ✅ Created
├── CASE_LAW_INTEGRATION_PLAN.md        ✅ Created
├── CASE_LAW_MVP_STATUS.md              ✅ Created (this file)
├── scrapers/
│   ├── case_law_discoverer.py          ✅ Created
│   ├── case_law_scraper.py             ⏳ TODO
│   ├── ag_opinion_discoverer.py        ⏳ TODO
│   ├── ag_opinion_scraper.py           ⏳ TODO
│   └── case_law_embedder.py            ⏳ TODO
└── discovered_cases.json               ⏳ Will be generated
```

---

## 🎯 Immediate Next Actions

### For You:
1. **Run SQL in Supabase** (`case_law_schema.sql`)
2. **Run discovery crawler** to find all CiteIDs
   ```bash
   python scrapers/case_law_discoverer.py
   ```

### For Me (Next Session):
1. Build case law scraper/parser
2. Build AG opinion discoverer/scraper
3. Build embedding generator
4. Integrate search into app

---

## 💡 Key Design Decisions Made

### 1. MVP Scope: 2020-2025
- **Why:** Recent cases most valuable, lower cost
- **Benefit:** Faster delivery, proves concept
- **Future:** Easy to backfill older cases

### 2. Separate Pinecone Indexes
- **Structure:**
  - `oklahoma-cases` (new)
  - `oklahoma-ag-opinions` (new)
  - `oklahoma-statutes` (existing)
  - `oklahoma-constitution` (existing)
- **Why:** Easier to manage, better performance
- **Future:** Can consolidate if needed

### 3. Intelligent Chunking
- **Strategy:** Split by opinion structure (syllabus, facts, discussion, holding)
- **Chunk Size:** 1,000-2,000 tokens
- **Overlap:** 200 tokens
- **Why:** Preserves context, improves search quality

### 4. Citation Cross-Referencing
- **Plan:** Extract statute/case citations from opinions
- **Benefit:** Show "Cases citing this statute"
- **Implementation:** Later phase (not MVP)

---

## 📚 Documentation References

- **Full Plan:** `CASE_LAW_INTEGRATION_PLAN.md`
- **OSCN URLs:**
  - Case Law Index: https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKCS&level=1
  - AG Opinions Index: https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKAG&level=1

---

## Questions?

**Q: How long will the full scrape take?**
A: With rate limiting (2 seconds/request), expect 12-24 hours for ~15K-20K cases.

**Q: Can we run this faster?**
A: We could use multiple workers, but want to be respectful to OSCN servers.

**Q: What if a scrape fails midway?**
A: The scraper will track progress and can resume from where it left off.

**Q: How do we handle updates (new cases)?**
A: Run discovery weekly/monthly to find new CiteIDs, scrape only new ones.

---

## Success Criteria

### MVP Success = All 3 Achieved:
1. ✅ Database schema created
2. ⏳ 2020-2025 cases scraped and stored
3. ⏳ Search returns relevant cases for user queries

### Stretch Goals:
- Citation cross-referencing (show related cases/statutes)
- "Similar cases" feature
- Judge/court analytics

Ready to proceed! Let me know when you've run the SQL schema and we can start the discovery crawler. 🚀
