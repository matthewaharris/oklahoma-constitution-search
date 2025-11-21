#!/usr/bin/env python3
"""
Check what's in Supabase for specific cite_ids
"""
from supabase import create_client

try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    from config_production import SUPABASE_URL, SUPABASE_KEY

print("=" * 70)
print("CHECKING SUPABASE FOR CITE IDS")
print("=" * 70)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# The cite_ids that Pinecone returns (CORRECT)
correct_cite_ids = ["455331", "71829", "71823", "104214", "455430"]

print("\nChecking what's in Supabase for these cite_ids:")
print("-" * 70)

for cite_id in correct_cite_ids:
    try:
        result = supabase.table('statutes').select(
            'cite_id, page_title, title_number, section_number, main_text'
        ).eq('cite_id', cite_id).limit(1).execute()

        if result.data and len(result.data) > 0:
            doc = result.data[0]
            print(f"\nCite ID: {cite_id}")
            print(f"  Title: {doc.get('title_number', 'N/A')}, Section: {doc.get('section_number', 'N/A')}")
            print(f"  Page Title: {doc.get('page_title', 'Untitled')[:80]}")
            print(f"  Text preview: {doc.get('main_text', '')[:150]}...")
        else:
            print(f"\nCite ID: {cite_id} - NOT FOUND IN SUPABASE!")
    except Exception as e:
        print(f"\nCite ID: {cite_id} - ERROR: {e}")

print("\n" + "=" * 70)
print("CHECKING OLD/WRONG CITE IDS FROM PRODUCTION")
print("=" * 70)

# From your production logs - these were the wrong results
wrong_cite_ids_from_production = ["85091", "85009", "85110"]

print("\nWhat's in Supabase for the OLD cite_ids production was using:")
print("-" * 70)

for cite_id in wrong_cite_ids_from_production:
    try:
        result = supabase.table('statutes').select(
            'cite_id, page_title, title_number, section_number, main_text'
        ).eq('cite_id', cite_id).limit(1).execute()

        if result.data and len(result.data) > 0:
            doc = result.data[0]
            print(f"\nCite ID: {cite_id}")
            print(f"  Title: {doc.get('title_number', 'N/A')}, Section: {doc.get('section_number', 'N/A')}")
            print(f"  Page Title: {doc.get('page_title', 'Untitled')[:80]}")
            print(f"  Text preview: {doc.get('main_text', '')[:150]}...")
        else:
            print(f"\nCite ID: {cite_id} - NOT FOUND IN SUPABASE!")
    except Exception as e:
        print(f"\nCite ID: {cite_id} - ERROR: {e}")

print("\n" + "=" * 70)
