#!/usr/bin/env python3
"""
Simple PDF processor for Oklahoma Constitution using only PyPDF2
"""

import re
import json
from pathlib import Path
from supabase_client import StatutesDatabase

class SimplePDFProcessor:
    def __init__(self):
        self.db = StatutesDatabase()

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
            print("PyPDF2 not found. Installing...")
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
                            full_text += text + "\n\n"
                    except Exception as e:
                        print(f"    Error on page {i+1}: {e}")

            print(f"✓ Extracted {len(full_text)} characters of text")

            # Save raw text
            with open('constitution_raw_text.txt', 'w', encoding='utf-8') as f:
                f.write(full_text)

            print("✓ Saved raw text to: constitution_raw_text.txt")

            return full_text

        except Exception as e:
            print(f"❌ Error extracting text from PDF: {e}")
            return None

    def parse_constitution_manually(self, text):
        """Parse constitution with simple regex patterns"""

        print("Parsing constitution structure...")

        # Clean up the text a bit
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace

        sections = []

        # Look for Article headers
        article_patterns = [
            r'ARTICLE\s+([IVXLC]+|\d+)[.\s]*[-–—]?\s*([^\n]+)',
            r'Article\s+([IVXLC]+|\d+)[.\s]*[-–—]?\s*([^\n]+)',
        ]

        # Look for Section headers
        section_patterns = [
            r'(?:SECTION|Section|Sec\.?)\s+(\d+[a-zA-Z]?)[.\s]*[-–—]?\s*([^\n]+)',
            r'§\s*(\d+[a-zA-Z]?)[.\s]*[-–—]?\s*([^\n]+)',
        ]

        # Find all potential headers
        all_matches = []

        for pattern in article_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                all_matches.append({
                    'type': 'article',
                    'number': match.group(1),
                    'title': match.group(2).strip(),
                    'start': match.start(),
                    'end': match.end()
                })

        for pattern in section_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                all_matches.append({
                    'type': 'section',
                    'number': match.group(1),
                    'title': match.group(2).strip(),
                    'start': match.start(),
                    'end': match.end()
                })

        # Sort by position in text
        all_matches.sort(key=lambda x: x['start'])

        print(f"Found {len(all_matches)} potential sections:")

        # Extract content for each section
        for i, match in enumerate(all_matches):

            # Get content from end of current header to start of next header
            content_start = match['end']
            if i + 1 < len(all_matches):
                content_end = all_matches[i + 1]['start']
            else:
                content_end = len(text)

            content = text[content_start:content_end].strip()

            # Clean up content
            content = re.sub(r'\s+', ' ', content)  # Normalize whitespace

            section_data = {
                'type': match['type'],
                'number': match['number'],
                'title': match['title'],
                'content': content[:2000],  # Limit content length
                'full_content': content
            }

            sections.append(section_data)

            print(f"  {match['type'].title()} {match['number']}: {match['title'][:50]}...")

        print(f"✓ Parsed {len(sections)} constitution sections")

        # Save parsed data
        with open('constitution_sections_simple.json', 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)

        print("✓ Saved parsed sections to: constitution_sections_simple.json")

        return sections

    def update_database_with_pdf_data(self, sections):
        """Update database records with PDF data"""

        print(f"Updating database with {len(sections)} constitution sections...")

        # Get existing cite IDs that need updating
        try:
            result = self.db.client.table('statutes').select('cite_id, page_title, main_text').execute()
            existing_records = result.data

            # Find records with NULL or Turnstile data
            bad_records = []
            for record in existing_records:
                cite_id = record['cite_id']
                page_title = record.get('page_title', '') or ''
                main_text = record.get('main_text', '') or ''

                if ('turnstile' in page_title.lower() or
                    not main_text or
                    main_text.strip() == ''):
                    bad_records.append(cite_id)

            print(f"Found {len(bad_records)} records that need updating")

        except Exception as e:
            print(f"Error getting existing records: {e}")
            bad_records = []

        updated_count = 0
        created_count = 0

        # Update records with PDF content
        for i, section in enumerate(sections):
            try:
                # Determine cite_id - use existing bad records first
                if i < len(bad_records):
                    cite_id = bad_records[i]
                    update_existing = True
                else:
                    # Create new cite_id for additional sections
                    cite_id = str(600000 + i)  # Use a high range for constitution
                    update_existing = False

                # Prepare statute data
                statute_data = {
                    'title_number': 'CONST',
                    'title_name': 'Oklahoma Constitution',
                    'chapter_number': None,
                    'chapter_name': None,
                    'article_number': section['number'] if section['type'] == 'article' else None,
                    'article_name': section['title'] if section['type'] == 'article' else None,
                    'section_number': section['number'] if section['type'] == 'section' else None,
                    'section_name': section['title'],
                    'page_title': section['title'],
                    'title_bar': f"Oklahoma Constitution - {section['title']}",
                    'citation_format': f"OK Const. {section['type']} {section['number']}",
                    'main_text': section['full_content'],
                    'full_json': {
                        'cite_id': cite_id,
                        'metadata': {
                            'title_number': 'CONST',
                            'title_name': 'Oklahoma Constitution',
                            'section_name': section['title'],
                        },
                        'content': {
                            'main_text': section['full_content'],
                            'paragraphs': [{'text': section['full_content'], 'is_historical': False}]
                        },
                        'source': 'pdf_processing',
                        'scraper_version': '1.3'
                    },
                    'scraper_version': '1.3_pdf'
                }

                if update_existing:
                    # Update existing record
                    result = self.db.client.table('statutes').update(statute_data).eq('cite_id', cite_id).execute()

                    if result.data:
                        print(f"  ✓ Updated CiteID {cite_id}: {section['title'][:40]}...")
                        updated_count += 1
                    else:
                        print(f"  ❌ Failed to update CiteID {cite_id}")

                else:
                    # Create new record
                    statute_data['cite_id'] = cite_id
                    statute_data['url'] = f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}"

                    result = self.db.client.table('statutes').insert(statute_data).execute()

                    if result.data:
                        print(f"  ✓ Created CiteID {cite_id}: {section['title'][:40]}...")
                        created_count += 1
                    else:
                        print(f"  ❌ Failed to create CiteID {cite_id}")

            except Exception as e:
                print(f"  ❌ Error processing section {i}: {e}")

        print(f"\n" + "="*50)
        print("DATABASE UPDATE COMPLETED")
        print("="*50)
        print(f"Records updated: {updated_count}")
        print(f"Records created: {created_count}")
        print(f"Total processed: {updated_count + created_count}")

        # Show updated database stats
        try:
            stats = self.db.get_database_stats()
            print(f"\nDatabase now contains:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Error getting database stats: {e}")

def main():
    print("Simple Oklahoma Constitution PDF Processor")
    print("=" * 50)

    processor = SimplePDFProcessor()

    # Find PDF files
    pdf_files = processor.find_pdf_files()

    if not pdf_files:
        print("❌ No PDF files found in current directory")
        print("\nPlease copy your Oklahoma Constitution PDF to this folder and run again")
        return

    # Choose PDF file
    if len(pdf_files) == 1:
        chosen_pdf = pdf_files[0]
        print(f"\nUsing: {chosen_pdf}")
    else:
        print(f"\nWhich PDF would you like to process?")
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"{i}. {pdf_file.name}")

        choice = input("Enter number: ").strip()
        try:
            chosen_pdf = pdf_files[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid choice")
            return

    # Extract text from PDF
    text = processor.extract_text_from_pdf(chosen_pdf)

    if not text:
        print("❌ Failed to extract text from PDF")
        return

    # Parse constitution structure
    sections = processor.parse_constitution_manually(text)

    if not sections:
        print("❌ No constitution sections found")
        return

    print(f"\nFound {len(sections)} constitution sections")

    # Show some examples
    for section in sections[:5]:
        print(f"  {section['type'].title()} {section['number']}: {section['title']}")

    # Ask if user wants to update database
    response = input(f"\nUpdate database with these {len(sections)} sections? (y/n): ").lower()

    if response == 'y':
        processor.update_database_with_pdf_data(sections)
        print("\n✓ Database update completed!")
        print("Run 'python show_data.py' to see your updated constitution data")
    else:
        print("Database update cancelled")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()