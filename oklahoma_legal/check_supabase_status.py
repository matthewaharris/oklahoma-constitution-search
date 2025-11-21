"""
Check the current status of Supabase database
"""
import os
from supabase import create_client, Client

# Try environment variables first, then config file
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        import config
        SUPABASE_URL = config.SUPABASE_URL
        SUPABASE_KEY = config.SUPABASE_KEY
        print("Using credentials from config.py")
    except ImportError:
        print("ERROR: Could not load credentials from environment or config.py")
        exit(1)

# Create client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("SUPABASE DATABASE STATUS CHECK")
print("=" * 70)

# Check if tables exist and get counts
tables_to_check = [
    'statutes',
    'statute_paragraphs',
    'statute_definitions',
    'legislative_history',
    'statute_citations',
    'superseded_documents'
]

print("\nTable Status:")
print("-" * 70)

for table in tables_to_check:
    try:
        # Try to count records
        response = supabase.table(table).select('*', count='exact').limit(1).execute()
        count = response.count if hasattr(response, 'count') else 0
        print(f"{table:30} {count:>10,} records")
    except Exception as e:
        print(f"{table:30} ERROR: {str(e)[:40]}")

# Get sample statute if any exist
print("\n" + "=" * 70)
print("SAMPLE DATA")
print("=" * 70)

try:
    response = supabase.table('statutes').select('cite_id, title_number, section_number, page_title').limit(3).execute()
    if response.data:
        print("\nSample statutes:")
        for item in response.data:
            print(f"  CiteID {item['cite_id']}: Title {item.get('title_number')} §{item.get('section_number')} - {item.get('page_title', 'N/A')[:50]}")
    else:
        print("\nNo statutes found in database")
except Exception as e:
    print(f"\nError fetching sample: {e}")

print("\n" + "=" * 70)
