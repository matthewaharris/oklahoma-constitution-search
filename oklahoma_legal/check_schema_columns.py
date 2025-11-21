"""
Check if required columns exist in Supabase schema
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
print("SCHEMA COLUMN CHECK")
print("=" * 70)

# Try to insert a test record with the new columns
test_record = {
    'cite_id': 'TEST_SCHEMA_CHECK',
    'url': 'https://test.com',
    'document_type': 'constitution',
    'article_number': 'X',
    'article_name': 'Test Article',
    'main_text': 'Test text',
}

print("\nChecking if document_type and article columns exist...")

try:
    # Try to insert
    response = supabase.table('statutes').insert(test_record).execute()

    # Delete the test record
    supabase.table('statutes').delete().eq('cite_id', 'TEST_SCHEMA_CHECK').execute()

    print("\n SUCCESS: All required columns exist!")
    print("\nYou can proceed with uploading data.")

except Exception as e:
    error_msg = str(e)

    if 'column "document_type" of relation "statutes" does not exist' in error_msg:
        print("\n MISSING: document_type column")
        print("\nAction required:")
        print("1. Go to your Supabase dashboard: https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Run the contents of 'add_missing_columns.sql'")
        print("\nAfter running the SQL, run this script again to verify.")

    elif 'article' in error_msg.lower():
        print("\n MISSING: article_number or article_name columns")
        print("\nAction required: Run add_missing_columns.sql in Supabase SQL Editor")

    else:
        print(f"\n ERROR: {error_msg}")
        print("\nThis might be a different issue. Please check the error message.")

print("\n" + "=" * 70)
