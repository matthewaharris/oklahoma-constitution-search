#!/usr/bin/env python3
"""
Fresh start: Clear database and rebuild from Oklahoma Constitution PDF
"""

import re
import json
from pathlib import Path
from supabase_client import StatutesDatabase

class FreshConstitutionBuilder:
    def __init__(self):
        self.db = StatutesDatabase()

    def clear_all_data(self):
        """Delete ALL existing data from the database"""
        print("WARNING: This will delete ALL data from your database!")
        print("This includes:")
        print("- All statutes (constitution and regular statutes)")
        print("- All definitions")
        print("- All paragraphs")
        print("- All legislative history")
        print("- All citations")

        confirm = input("\nAre you sure you want to delete everything? (type 'DELETE ALL' to confirm): ")

        if confirm != "DELETE ALL":
            print("❌ Operation cancelled")
            return False

        print("\nDeleting all data...")

        try:
            # Delete in order to respect foreign key constraints
            tables_to_clear = [
                'superseded_documents',
                'statute_citations',
                'legislative_history',
                'statute_definitions',
                'statute_paragraphs',
                'statutes'
            ]

            for table in tables_to_clear:
                print(f"  Clearing {table}...")

                # First check if table has any data
                check_result = self.db.client.table(table).select('id').limit(1).execute()

                if check_result.data:
                    # Use a more reliable approach to delete all records
                    # Get all IDs and delete them
                    all_records = self.db.client.table(table).select('id').execute()

                    if all_records.data:
                        record_ids = [record['id'] for record in all_records.data]
                        print(f"    Deleting {len(record_ids)} records from {table}...")

                        # Delete in batches to avoid large requests
                        batch_size = 100
                        for i in range(0, len(record_ids), batch_size):
                            batch_ids = record_ids[i:i+batch_size]
                            self.db.client.table(table).delete().in_('id', batch_ids).execute()
                            print(f"      Deleted batch {i//batch_size + 1}")

                    print(f"    ✓ Cleared {table}")
                else:
                    print(f"    ✓ {table} was already empty")

            print("✓ All data deleted successfully")
            return True

        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            return False

    def find_pdf_files(self):
        """Find PDF files in the current directory"""
        current_dir = Path('.')
        pdf_files = list(current_dir.glob('*.pdf'))

        print(f"Found {len(pdf_files)} PDF files:")
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"  {i}. {pdf_file.name}")

        return pdf_files

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF using PyPDF2"""
        try:
            import PyPDF2
        except ImportError:
            print("Installing PyPDF2...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyPDF2'])
            import PyPDF2

        print(f"Extracting text from: {pdf_path}")

        full_text = ""

        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                print(f"PDF has {len(reader.pages)} pages")

                for i, page in enumerate(reader.pages):
                    print(f"  Processing page {i+1}/{len(reader.pages)}")
                    try:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n\n=== PAGE BREAK ===\n\n"
                    except Exception as e:
                        print(f"    Error on page {i+1}: {e}")

            print(f"✓ Extracted {len(full_text)} characters of text")

            # Save raw text with better formatting
            with open('constitution_full_text.txt', 'w', encoding='utf-8') as f:
                f.write(full_text)

            print("✓ Saved raw text to: constitution_full_text.txt")

            return full_text

        except Exception as e:
            print(f"❌ Error extracting text from PDF: {e}")
            return None

    def parse_constitution_structure(self, text):
        """Parse the constitution into articles and sections"""

        print("Parsing Oklahoma Constitution structure...")

        # Clean up text
        text = re.sub(r'=== PAGE BREAK ===', '\n', text)  # Remove page break markers

        # Split into logical sections
        sections = []

        # First, let's try to identify the main structure patterns
        # Oklahoma Constitution typically has:
        # - Preamble
        # - Articles (I, II, III, etc.)
        # - Sections within articles

        # Look for Preamble
        preamble_match = re.search(r'(PREAMBLE|Preamble)\s*(.*?)(?=ARTICLE|Article|$)', text, re.IGNORECASE | re.DOTALL)
        if preamble_match:
            preamble_text = preamble_match.group(2).strip()
            sections.append({
                'type': 'preamble',
                'article_number': None,
                'section_number': None,
                'title': 'Preamble',
                'content': preamble_text
            })
            print("  ✓ Found Preamble")

        # Look for Articles with Roman numerals or numbers
        article_pattern = r'ARTICLE\s+((?:[IVXLCDM]+|\d+))\s*[-.\s]*\s*([^\n\r]*?)(?=\n|\r)'
        article_matches = list(re.finditer(article_pattern, text, re.IGNORECASE | re.MULTILINE))

        print(f"  Found {len(article_matches)} articles")

        current_article = None

        for i, article_match in enumerate(article_matches):
            article_number = article_match.group(1).strip()
            article_title = article_match.group(2).strip()
            article_start = article_match.end()

            # Find the end of this article (start of next article or end of text)
            if i + 1 < len(article_matches):
                article_end = article_matches[i + 1].start()
            else:
                article_end = len(text)

            article_content = text[article_start:article_end]

            current_article = {
                'type': 'article',
                'article_number': article_number,
                'section_number': None,
                'title': article_title,
                'content': article_content[:500]  # Preview only
            }

            sections.append(current_article)
            print(f"    Article {article_number}: {article_title}")

            # Look for sections within this article
            section_pattern = r'(?:SECTION|Section|Sec\.?|§)\s+(\d+[a-zA-Z]?)\s*[-.\s]*\s*([^\n\r]*?)(?=\n|\r)'
            section_matches = list(re.finditer(section_pattern, article_content, re.IGNORECASE | re.MULTILINE))

            for j, section_match in enumerate(section_matches):
                section_number = section_match.group(1).strip()
                section_title = section_match.group(2).strip()
                section_start = section_match.end()

                # Find content until next section or end of article
                if j + 1 < len(section_matches):
                    section_end = section_matches[j + 1].start()
                else:
                    section_end = len(article_content)

                section_content = article_content[section_start:section_end].strip()

                sections.append({
                    'type': 'section',
                    'article_number': article_number,
                    'section_number': section_number,
                    'title': section_title,
                    'content': section_content
                })

                print(f"      Section {section_number}: {section_title[:60]}...")

        print(f"✓ Parsed {len(sections)} total constitution parts")

        # Save parsed structure
        with open('constitution_parsed_structure.json', 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)

        print("✓ Saved structure to: constitution_parsed_structure.json")

        return sections

    def insert_fresh_constitution_data(self, sections):
        """Insert all constitution data as fresh records"""

        print(f"\nInserting {len(sections)} constitution sections into database...")

        inserted_count = 0
        errors = []

        for i, section in enumerate(sections):
            try:
                # Create unique cite ID starting from 700000
                cite_id = str(700000 + i)

                # Build section name
                if section['type'] == 'preamble':
                    section_name = 'Preamble'
                    full_title = 'Oklahoma Constitution - Preamble'
                elif section['type'] == 'article':
                    section_name = f"Article {section['article_number']}"
                    if section['title']:
                        section_name += f" - {section['title']}"
                    full_title = f"Oklahoma Constitution - {section_name}"
                elif section['type'] == 'section':
                    section_name = f"Section {section['section_number']}"
                    if section['title']:
                        section_name += f" - {section['title']}"
                    full_title = f"Oklahoma Constitution - Article {section['article_number']}, {section_name}"

                # Create statute record
                statute_data = {
                    'cite_id': cite_id,
                    'url': f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}",
                    'title_number': 'CONST',
                    'title_name': 'Oklahoma Constitution',
                    'chapter_number': None,
                    'chapter_name': None,
                    'article_number': section.get('article_number'),
                    'article_name': section['title'] if section['type'] == 'article' else None,
                    'section_number': section.get('section_number'),
                    'section_name': section_name,
                    'page_title': full_title,
                    'title_bar': 'Oklahoma Constitution',
                    'citation_format': f"OK Const. {section_name}",
                    'main_text': section['content'],
                    'full_json': {
                        'cite_id': cite_id,
                        'metadata': {
                            'title_number': 'CONST',
                            'title_name': 'Oklahoma Constitution',
                            'article_number': section.get('article_number'),
                            'section_number': section.get('section_number'),
                            'section_name': section_name,
                        },
                        'content': {
                            'main_text': section['content'],
                            'paragraphs': [{'text': section['content'], 'is_historical': False}]
                        },
                        'source': 'pdf_fresh',
                        'scraper_version': '2.0'
                    },
                    'scraper_version': '2.0_fresh'
                }

                # Insert the record
                result = self.db.client.table('statutes').insert(statute_data).execute()

                if result.data:
                    print(f"  ✓ Inserted {cite_id}: {section_name}")
                    inserted_count += 1

                    # Also insert paragraph data
                    statute_id = result.data[0]['id']
                    paragraph_data = {
                        'statute_id': statute_id,
                        'paragraph_number': 1,
                        'text': section['content'],
                        'is_historical': False
                    }

                    self.db.client.table('statute_paragraphs').insert(paragraph_data).execute()

                else:
                    error_msg = f"Failed to insert {cite_id}: {section_name}"
                    errors.append(error_msg)
                    print(f"  ❌ {error_msg}")

            except Exception as e:
                error_msg = f"Error inserting section {i}: {e}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")

        print(f"\n" + "="*60)
        print("FRESH CONSTITUTION INSERT COMPLETED")
        print("="*60)
        print(f"Successfully inserted: {inserted_count}")
        print(f"Errors: {len(errors)}")

        if errors:
            print("\nErrors:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  {error}")

        # Save results
        results = {
            'inserted_count': inserted_count,
            'error_count': len(errors),
            'errors': errors
        }

        with open('fresh_constitution_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nResults saved to: fresh_constitution_results.json")

        return inserted_count

def main():
    print("Fresh Oklahoma Constitution Database Builder")
    print("=" * 60)

    builder = FreshConstitutionBuilder()

    # Find PDF files
    pdf_files = builder.find_pdf_files()

    if not pdf_files:
        print("❌ No PDF files found in current directory")
        print("Please copy your Oklahoma Constitution PDF to this folder")
        return

    # Choose PDF
    if len(pdf_files) == 1:
        chosen_pdf = pdf_files[0]
    else:
        print("\nWhich PDF contains the Oklahoma Constitution?")
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"{i}. {pdf_file.name}")

        choice = input("Enter number: ").strip()
        try:
            chosen_pdf = pdf_files[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid choice")
            return

    print(f"\nUsing PDF: {chosen_pdf}")

    # Step 1: Clear existing data
    print(f"\nSTEP 1: Clear existing database")
    if not builder.clear_all_data():
        return

    # Step 2: Extract text from PDF
    print(f"\nSTEP 2: Extract text from PDF")
    text = builder.extract_text_from_pdf(chosen_pdf)
    if not text:
        return

    # Step 3: Parse constitution structure
    print(f"\nSTEP 3: Parse constitution structure")
    sections = builder.parse_constitution_structure(text)
    if not sections:
        return

    # Step 4: Insert fresh data
    print(f"\nSTEP 4: Insert fresh constitution data")
    inserted_count = builder.insert_fresh_constitution_data(sections)

    # Step 5: Show final results
    print(f"\n" + "="*60)
    print("FRESH CONSTITUTION DATABASE COMPLETE!")
    print("="*60)

    try:
        stats = builder.db.get_database_stats()
        print(f"Final database contents:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error getting final stats: {e}")

    print(f"\nNext steps:")
    print(f"1. Run 'python show_data.py' to see your new constitution database")
    print(f"2. Check 'constitution_full_text.txt' for raw extracted text")
    print(f"3. Check 'constitution_parsed_structure.json' for parsed structure")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()