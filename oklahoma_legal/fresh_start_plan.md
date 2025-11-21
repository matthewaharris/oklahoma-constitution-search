# Fresh Start - Complete Oklahoma Legal Database

## Current Status
- **Constitution**: Previously parsed from PDF, needs to be scraped from OSCN
- **Title 10**: 982 files downloaded (will be re-scraped)
- **Titles 1-9, 11-85**: Empty directories, need scraping

## Plan Overview

### Phase 1: Backup & Clean
1. Archive existing Title 10 data (already done)
2. Clear statute_html directory
3. Clear Pinecone indexes
4. Truncate Supabase tables

### Phase 2: Scrape Everything from OSCN
1. **Constitution** - Special handling (different structure)
2. **Statutes Titles 10-85** - Regular statute structure
3. Store all as raw HTML files

### Phase 3: Process Everything
1. Process Constitution HTML → Supabase + Pinecone
2. Process all Statute titles → Supabase + Pinecone
3. Archive all raw data

## OSCN Structure

### Constitution URL Pattern
The Oklahoma Constitution is at:
- Main index: https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKST&level=1
- Individual articles: https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID=XXXXX

Constitution has 31 Articles (not "Titles")

### Statutes URL Pattern
Oklahoma Statutes have 85 Titles:
- Title index: https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKST10&level=1
- Individual sections: https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID=XXXXX

## Scripts Needed

1. **clear_data.py** - Safely backup and clear existing data
2. **scrape_constitution.py** - Special scraper for Constitution articles
3. **scrape_all_titles.py** - Automated scraper for all 85 titles
4. **process_all.py** - Process everything to Supabase + Pinecone

## Execution Order

```bash
# 1. Backup current data (optional, already have archive)
python archive_raw_data.py

# 2. Clear old data
python clear_data.py --confirm

# 3. Scrape Constitution (once IP whitelisted)
python scrape_constitution.py

# 4. Scrape all Statute titles (once IP whitelisted)
python scrape_all_titles.py --start 10 --end 85

# 5. Process everything
python process_all.py --include-constitution

# 6. Archive everything
python archive_raw_data.py --all
```

## Data Organization

```
statute_html/
├── constitution/          # Oklahoma Constitution (31 articles)
│   ├── article_01.html
│   ├── article_01.meta.json
│   └── ...
│
└── title_XX/             # Statutes by title
    ├── cite_XXXXX.html
    └── cite_XXXXX.meta.json
```

## Important Notes

- **Constitution** has different structure than statutes
- Constitution uses "Articles" not "Titles"
- Need special parser for Constitution HTML
- Estimate: ~10,000-15,000 total statute sections across 85 titles
- Cost: ~$1-2 for all embeddings (OpenAI API)
