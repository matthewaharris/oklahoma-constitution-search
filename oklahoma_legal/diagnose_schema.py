"""
Diagnose exactly what columns exist in the statutes table
"""
import os
from supabase import create_client, Client

# Load credentials
try:
    import config
    SUPABASE_URL = config.SUPABASE_URL
    SUPABASE_KEY = config.SUPABASE_KEY
except ImportError:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("DETAILED SCHEMA DIAGNOSIS")
print("=" * 70)

# Query the information schema to see what columns actually exist
query = """
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'statutes'
ORDER BY ordinal_position;
"""

print("\nQuerying information_schema.columns for 'statutes' table...")

try:
    # Execute raw SQL query
    response = supabase.rpc('exec_sql', {'query': query}).execute()
    print(f"\nResponse: {response}")
except Exception as e:
    print(f"\nDirect query not supported. Error: {e}")
    print("\nTrying alternative method: inserting test records...")

# Alternative: Try inserting records with different column combinations
print("\n" + "=" * 70)
print("TESTING COLUMN AVAILABILITY")
print("=" * 70)

# Test 1: Basic columns only
print("\n1. Testing basic columns (cite_id, url, main_text)...")
try:
    test1 = {
        'cite_id': '999991',
        'url': 'https://test.com',
        'main_text': 'Test'
    }
    supabase.table('statutes').insert(test1).execute()
    supabase.table('statutes').delete().eq('cite_id', '999991').execute()
    print("   OK Basic columns work")
except Exception as e:
    print(f"   FAILED: {e}")

# Test 2: With document_type
print("\n2. Testing document_type column...")
try:
    test2 = {
        'cite_id': '999992',
        'url': 'https://test.com',
        'main_text': 'Test',
        'document_type': 'constitution'
    }
    supabase.table('statutes').insert(test2).execute()
    supabase.table('statutes').delete().eq('cite_id', '999992').execute()
    print("   OK document_type column exists")
except Exception as e:
    print(f"   FAILED document_type: {e}")

# Test 3: With article_number
print("\n3. Testing article_number column...")
try:
    test3 = {
        'cite_id': '999993',
        'url': 'https://test.com',
        'main_text': 'Test',
        'article_number': 'X'
    }
    supabase.table('statutes').insert(test3).execute()
    supabase.table('statutes').delete().eq('cite_id', '999993').execute()
    print("   OK article_number column exists")
except Exception as e:
    print(f"   FAILED article_number: {e}")

# Test 4: With article_name
print("\n4. Testing article_name column...")
try:
    test4 = {
        'cite_id': '999994',
        'url': 'https://test.com',
        'main_text': 'Test',
        'article_name': 'Test Article'
    }
    supabase.table('statutes').insert(test4).execute()
    supabase.table('statutes').delete().eq('cite_id', '999994').execute()
    print("   OK article_name column exists")
except Exception as e:
    print(f"   FAILED article_name: {e}")

# Test 5: All together
print("\n5. Testing all new columns together...")
try:
    test5 = {
        'cite_id': '999995',
        'url': 'https://test.com',
        'main_text': 'Test',
        'document_type': 'constitution',
        'article_number': 'X',
        'article_name': 'Test Article'
    }
    supabase.table('statutes').insert(test5).execute()
    supabase.table('statutes').delete().eq('cite_id', '999995').execute()
    print("   OK ALL columns work together!")
    print("\n   SUCCESS: Schema is ready for data upload!")
except Exception as e:
    print(f"   FAILED Combined test: {e}")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
