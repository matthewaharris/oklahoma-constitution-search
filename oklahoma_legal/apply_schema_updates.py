"""
Apply schema improvements to Supabase
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

# Create client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("APPLYING SCHEMA UPDATES TO SUPABASE")
print("=" * 70)

# Read the SQL file
with open('schema_improvements.sql', 'r') as f:
    sql_content = f.read()

print("\nExecuting schema updates...")
print("(This will add document_type, article fields, and views)")

try:
    # Execute the SQL
    response = supabase.rpc('exec_sql', {'sql': sql_content}).execute()
    print("\nSUCCESS: Schema updates applied!")
except Exception as e:
    print(f"\nNote: RPC method not available. Applying updates via API...")
    print(f"Error: {e}")
    print("\nThe schema updates need to be applied through the Supabase SQL Editor.")
    print("Please run the contents of schema_improvements.sql in the Supabase dashboard.")

print("\n" + "=" * 70)
