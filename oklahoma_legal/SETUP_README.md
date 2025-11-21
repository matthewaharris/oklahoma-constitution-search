# Oklahoma Statutes Scraper with Supabase Database

This project scrapes Oklahoma statutes from the OSCN (Oklahoma State Courts Network) website and stores them in a Supabase PostgreSQL database.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Supabase Database

1. **Log into your Supabase account** and go to your project dashboard
2. **Execute the database schema** by running the SQL in `database_schema.sql`:
   - Go to the SQL Editor in your Supabase dashboard
   - Copy and paste the contents of `database_schema.sql`
   - Run the script to create all tables, indexes, and policies

### 3. Configure Connection

1. **Copy the configuration template**:
   ```bash
   cp config_template.py config.py
   ```

2. **Edit `config.py`** with your actual Supabase credentials:
   ```python
   # Your actual Supabase project URL (found in Settings > API)
   SUPABASE_URL = "https://your-project-id.supabase.co"

   # Your anon key or service role key (found in Settings > API)
   SUPABASE_KEY = "your-anon-or-service-role-key-here"
   ```

**Security Note**: Never commit `config.py` to version control. Add it to `.gitignore`.

### 4. Test the Setup

Run the database connection test:
```bash
python supabase_client.py
```

This should output "Database connection successful!" and show basic stats.

## Usage

### Basic Scraping and Storage

**Scrape a single statute:**
```python
from integrated_scraper import IntegratedStatutesScraper

scraper = IntegratedStatutesScraper()
result = scraper.scrape_and_store_statute('440462')
print(result)
```

**Scrape multiple statutes:**
```python
cite_ids = ['440462', '123456', '789012']  # Add your cite IDs
results = scraper.bulk_scrape_statutes(cite_ids)
print(f"Scraped {results['successful']} statutes successfully")
```

**Test the integrated system:**
```bash
python integrated_scraper.py
```

### Database Queries

**Check what's been scraped:**
```python
from supabase_client import StatutesDatabase

db = StatutesDatabase()
stats = db.get_database_stats()
print(stats)
```

**Search statutes:**
```python
results = db.search_statutes("investment agreement")
for statute in results:
    print(f"{statute['cite_id']}: {statute['section_name']}")
```

**Get all statutes from a title:**
```python
title_68_statutes = db.get_statutes_by_title('68')
print(f"Found {len(title_68_statutes)} statutes in Title 68")
```

## Database Schema

The database is designed with the following main tables:

- **`statutes`**: Main statute information and metadata
- **`statute_paragraphs`**: Individual paragraphs of statute text
- **`statute_definitions`**: Structured definitions (for definition statutes)
- **`legislative_history`**: Bills, amendments, and effective dates
- **`statute_citations`**: Cross-references to other statutes
- **`superseded_documents`**: Links to older versions

## Key Features

✅ **Respectful Scraping**: Built-in delays between requests
✅ **Duplicate Detection**: Avoids re-scraping existing statutes
✅ **Structured Data**: Extracts definitions, paragraphs, and metadata
✅ **Full-Text Search**: Database supports searching statute content
✅ **Error Handling**: Robust error handling and logging
✅ **Flexible Storage**: Raw JSON data preserved alongside structured data

## Example Output

A scraped statute includes:

```json
{
  "cite_id": "440462",
  "metadata": {
    "title_number": "68",
    "title_name": "Revenue and Taxation",
    "chapter_number": "1",
    "section_number": "4103",
    "section_name": "Definitions"
  },
  "content": {
    "definitions": [
      {
        "number": "1",
        "term": "Capital costs",
        "definition": "costs for land, buildings, improvements..."
      }
    ],
    "main_text": "For purposes of the Oklahoma Specialized Quality Investment Act..."
  }
}
```

## Files Overview

- **`final_oklahoma_scraper.py`**: Core scraping logic with HTML parsing
- **`supabase_client.py`**: Database connection and data storage functions
- **`integrated_scraper.py`**: Combined scraper + database operations
- **`database_schema.sql`**: Complete database schema for Supabase
- **`config_template.py`**: Template for database configuration
- **`requirements.txt`**: Python package dependencies

## Troubleshooting

**"supabase-py not installed"**:
```bash
pip install supabase
```

**"config.py not found"**:
```bash
cp config_template.py config.py
# Then edit config.py with your credentials
```

**Database connection fails**:
- Check your Supabase URL and key in `config.py`
- Ensure your Supabase project is active
- Verify the database schema has been created

**Scraping fails**:
- Check your internet connection
- OSCN website may be temporarily unavailable
- Some cite IDs may not exist

## Rate Limiting

The scraper includes a default 1-second delay between requests to be respectful to the OSCN servers. You can adjust this:

```python
scraper = IntegratedStatutesScraper(delay_seconds=2.0)  # 2-second delay
```

## Legal Notice

This tool is for educational and research purposes. Please respect the OSCN website's terms of service and use reasonable rate limiting when scraping data.