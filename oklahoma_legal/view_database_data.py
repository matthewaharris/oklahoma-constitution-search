#!/usr/bin/env python3
"""
View and query the Oklahoma Statutes database data
"""

import json
from supabase_client import StatutesDatabase

def print_separator(title=""):
    print(f"\n{'='*60}")
    if title:
        print(f"{title:^60}")
        print('='*60)

def view_all_statutes():
    """Display overview of all statutes in the database"""
    db = StatutesDatabase()

    print_separator("ALL STATUTES OVERVIEW")

    # Get basic stats
    stats = db.get_database_stats()
    print(f"Database Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Get all statutes with basic info
    result = db.client.table('statutes').select(
        'cite_id, title_number, title_name, chapter_number, chapter_name, '
        'section_number, section_name, scraped_at'
    ).order('title_number', 'chapter_number', 'section_number').execute()

    if result.data:
        print(f"\nFound {len(result.data)} statutes:")
        print("-" * 100)
        print(f"{'Cite ID':<8} {'Title':<15} {'Chapter':<15} {'Section':<15} {'Name':<30} {'Scraped':<12}")
        print("-" * 100)

        for statute in result.data:
            title_info = f"{statute.get('title_number', 'N/A')}"
            chapter_info = f"{statute.get('chapter_number', 'N/A')}"
            section_info = f"{statute.get('section_number', 'N/A')}"
            name = (statute.get('section_name') or '')[:28] + '...' if len(statute.get('section_name') or '') > 28 else (statute.get('section_name') or '')
            scraped = statute.get('scraped_at', '')[:10] if statute.get('scraped_at') else 'N/A'

            print(f"{statute['cite_id']:<8} {title_info:<15} {chapter_info:<15} {section_info:<15} {name:<30} {scraped:<12}")

def view_statute_details(cite_id='440462'):
    """Display detailed information about a specific statute"""
    db = StatutesDatabase()

    print_separator(f"STATUTE {cite_id} DETAILS")

    # Get main statute info
    statute = db.get_statute(cite_id)
    if not statute:
        print(f"Statute {cite_id} not found!")
        return

    print("METADATA:")
    metadata_fields = [
        'title_number', 'title_name', 'chapter_number', 'chapter_name',
        'article_number', 'article_name', 'section_number', 'section_name',
        'citation_format'
    ]

    for field in metadata_fields:
        value = statute.get(field)
        if value:
            print(f"  {field.replace('_', ' ').title()}: {value}")

    # Show text preview
    main_text = statute.get('main_text', '')
    if main_text:
        print(f"\nMAIN TEXT PREVIEW ({len(main_text)} characters):")
        print(f"  {main_text[:300]}...")

    # Get definitions
    result = db.client.table('statute_definitions').select('*').eq('statute_id', statute['id']).order('definition_number').execute()
    if result.data:
        print(f"\nDEFINITIONS ({len(result.data)} found):")
        for defn in result.data:
            print(f"  {defn['definition_number']}. {defn['term']}")
            print(f"     {defn['definition'][:100]}...")
            print()

    # Get legislative history
    result = db.client.table('legislative_history').select('*').eq('statute_id', statute['id']).order('year').execute()
    if result.data:
        print(f"LEGISLATIVE HISTORY ({len(result.data)} entries):")
        for hist in result.data:
            bill = f"{hist.get('bill_type', '')} {hist.get('bill_number', '')}".strip()
            print(f"  {hist['year']}: {bill}")
            if hist.get('details'):
                print(f"    Details: {hist['details']}")
            if hist.get('effective_date'):
                print(f"    Effective: {hist['effective_date']}")
            print()

def view_definitions():
    """Display all definitions across all statutes"""
    db = StatutesDatabase()

    print_separator("ALL DEFINITIONS")

    result = db.client.table('statute_definitions').select(
        '*, statutes!inner(cite_id, section_name)'
    ).order('statute_id', 'definition_number').execute()

    if result.data:
        print(f"Found {len(result.data)} definitions:")
        print("-" * 80)
        print(f"{'Statute':<10} {'#':<3} {'Term':<25} {'Definition Preview':<40}")
        print("-" * 80)

        for defn in result.data:
            statute_info = defn.get('statutes', {})
            cite_id = statute_info.get('cite_id', 'N/A')
            term = (defn['term'][:23] + '..') if len(defn['term']) > 25 else defn['term']
            definition_preview = (defn['definition'][:37] + '...') if len(defn['definition']) > 40 else defn['definition']

            print(f"{cite_id:<10} {defn['definition_number']:<3} {term:<25} {definition_preview:<40}")

def search_statutes(search_term):
    """Search for statutes containing specific terms"""
    db = StatutesDatabase()

    print_separator(f"SEARCH RESULTS: '{search_term}'")

    results = db.search_statutes(search_term, limit=10)

    if results:
        print(f"Found {len(results)} matching statutes:")
        print("-" * 80)

        for result in results:
            cite_id = result.get('cite_id', 'N/A')
            section_name = result.get('section_name', 'N/A')
            # Show context around the search term
            main_text = result.get('main_text', '')
            search_lower = search_term.lower()
            text_lower = main_text.lower()

            if search_lower in text_lower:
                start_pos = max(0, text_lower.find(search_lower) - 50)
                end_pos = min(len(main_text), start_pos + 150)
                context = main_text[start_pos:end_pos]
                if start_pos > 0:
                    context = "..." + context
                if end_pos < len(main_text):
                    context = context + "..."
            else:
                context = main_text[:150] + "..."

            print(f"\n{cite_id}: {section_name}")
            print(f"  Context: {context}")
    else:
        print(f"No statutes found containing '{search_term}'")

def export_statute_json(cite_id='440462', output_file=None):
    """Export a statute's complete data as JSON"""
    db = StatutesDatabase()

    if not output_file:
        output_file = f"statute_{cite_id}_export.json"

    print_separator(f"EXPORTING STATUTE {cite_id}")

    # Get complete statute data
    statute = db.get_statute(cite_id)
    if not statute:
        print(f"Statute {cite_id} not found!")
        return

    # Get all related data
    export_data = {
        'statute': statute,
        'paragraphs': [],
        'definitions': [],
        'legislative_history': [],
        'citations': [],
        'superseded_documents': []
    }

    # Get related data
    tables = [
        ('paragraphs', 'statute_paragraphs'),
        ('definitions', 'statute_definitions'),
        ('legislative_history', 'legislative_history'),
        ('citations', 'statute_citations'),
        ('superseded_documents', 'superseded_documents')
    ]

    for key, table_name in tables:
        result = db.client.table(table_name).select('*').eq('statute_id', statute['id']).execute()
        export_data[key] = result.data

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"Statute {cite_id} exported to: {output_file}")
    print(f"Export includes:")
    for key, data in export_data.items():
        if key != 'statute':
            print(f"  - {len(data)} {key}")

def main():
    """Interactive menu to explore the database"""

    print("Oklahoma Statutes Database Viewer")
    print("=" * 40)

    while True:
        print("\nChoose an option:")
        print("1. View all statutes overview")
        print("2. View detailed statute info (default: 440462)")
        print("3. View all definitions")
        print("4. Search statutes")
        print("5. Export statute as JSON")
        print("6. Exit")

        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == '1':
            view_all_statutes()
        elif choice == '2':
            cite_id = input("Enter cite ID (press Enter for 440462): ").strip()
            cite_id = cite_id if cite_id else '440462'
            view_statute_details(cite_id)
        elif choice == '3':
            view_definitions()
        elif choice == '4':
            search_term = input("Enter search term: ").strip()
            if search_term:
                search_statutes(search_term)
        elif choice == '5':
            cite_id = input("Enter cite ID to export (press Enter for 440462): ").strip()
            cite_id = cite_id if cite_id else '440462'
            export_statute_json(cite_id)
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your database is set up correctly.")