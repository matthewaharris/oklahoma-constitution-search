#!/usr/bin/env python3
"""
Simple script to display all data in the Oklahoma Statutes database
"""

from supabase_client import StatutesDatabase

def show_all_data():
    """Display all stored data"""
    db = StatutesDatabase()

    print("OKLAHOMA STATUTES DATABASE CONTENTS")
    print("="*50)

    # Show database stats
    stats = db.get_database_stats()
    print(f"\nDATABASE STATISTICS:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Show all statutes
    print(f"\nALL STATUTES:")
    result = db.client.table('statutes').select('*').execute()

    for statute in result.data:
        print(f"\n--- STATUTE {statute['cite_id']} ---")
        print(f"Title: {statute.get('title_number')} - {statute.get('title_name')}")
        print(f"Chapter: {statute.get('chapter_number')} - {statute.get('chapter_name')}")
        print(f"Section: {statute.get('section_number')} - {statute.get('section_name')}")
        print(f"URL: {statute['url']}")
        print(f"Scraped: {statute['scraped_at']}")

        if statute.get('main_text'):
            print(f"Text Preview: {statute['main_text'][:200]}...")

        # Show definitions for this statute
        defs_result = db.client.table('statute_definitions').select('*').eq('statute_id', statute['id']).execute()
        if defs_result.data:
            print(f"\nDEFINITIONS ({len(defs_result.data)}):")
            for defn in defs_result.data:
                print(f"  {defn['definition_number']}. {defn['term']}: {defn['definition'][:100]}...")

        # Show legislative history
        hist_result = db.client.table('legislative_history').select('*').eq('statute_id', statute['id']).execute()
        if hist_result.data:
            print(f"\nLEGISLATIVE HISTORY ({len(hist_result.data)}):")
            for hist in hist_result.data:
                print(f"  {hist['year']}: {hist.get('bill_type', '')} {hist.get('bill_number', '')} - {hist.get('details', '')}")

        # Show citations
        cite_result = db.client.table('statute_citations').select('*').eq('statute_id', statute['id']).execute()
        if cite_result.data:
            print(f"\nCITATIONS ({len(cite_result.data)}):")
            for cite in cite_result.data:
                print(f"  {cite.get('citation_text', '')}: {cite.get('citation_name', '')}")

if __name__ == "__main__":
    try:
        show_all_data()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your database connection is working.")