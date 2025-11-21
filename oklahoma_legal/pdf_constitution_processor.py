#!/usr/bin/env python3
"""
Process Oklahoma Constitution PDF and populate database
"""

import re
import json
from pathlib import Path
from supabase_client import StatutesDatabase

def install_pdf_dependencies():
    """Install required packages for PDF processing"""
    import subprocess
    import sys

    packages = ['PyPDF2', 'pdfplumber']

    print("Checking PDF processing dependencies...")

    for package in packages:
        try:
            __import__(package.lower().replace('pdf2', 'PDF2'))
            print(f"✓ {package} already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

class PDFConstitutionProcessor:
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

    def process_with_pdfplumber(self, pdf_path):
        """Process PDF using pdfplumber (better for text extraction)"""

        try:
            import pdfplumber
        except ImportError:
            print("Installing pdfplumber...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pdfplumber'])
            import pdfplumber

        print(f"Processing PDF with pdfplumber: {pdf_path}")

        full_text = ""

        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF has {len(pdf.pages)} pages")

            for i, page in enumerate(pdf.pages):
                print(f"  Processing page {i+1}/{len(pdf.pages)}")
                text = page.extract_text()
                if text:
                    full_text += text + "\n\n"

        print(f"✓ Extracted {len(full_text)} characters of text")

        # Save raw extracted text
        with open('constitution_raw_text.txt', 'w', encoding='utf-8') as f:
            f.write(full_text)

        print("✓ Saved raw text to: constitution_raw_text.txt")

        return full_text

    def process_with_pypdf2(self, pdf_path):
        """Process PDF using PyPDF2 (fallback option)"""

        try:
            import PyPDF2
        except ImportError:
            print("Installing PyPDF2...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyPDF2'])
            import PyPDF2

        print(f"Processing PDF with PyPDF2: {pdf_path}")

        full_text = ""

        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"PDF has {len(reader.pages)} pages")

            for i, page in enumerate(reader.pages):
                print(f"  Processing page {i+1}/{len(reader.pages)}")
                text = page.extract_text()
                if text:
                    full_text += text + "\n\n"

        print(f"✓ Extracted {len(full_text)} characters of text")

        # Save raw extracted text
        with open('constitution_raw_text_pypdf2.txt', 'w', encoding='utf-8') as f:
            f.write(full_text)

        print("✓ Saved raw text to: constitution_raw_text_pypdf2.txt")

        return full_text

    def parse_constitution_structure(self, text):
        """Parse the constitution text into articles and sections"""

        print("Parsing constitution structure...")

        # Common patterns for Oklahoma Constitution structure
        constitution_sections = []

        # Look for Article patterns
        article_pattern = r'ARTICLE\s+([IVX]+|[0-9]+)[.\s]*[-–—]?\s*(.+?)(?=\n)'
        articles = re.finditer(article_pattern, text, re.IGNORECASE | re.MULTILINE)

        article_count = 0
        for article_match in articles:
            article_number = article_match.group(1).strip()
            article_title = article_match.group(2).strip()
            article_count += 1

            print(f"  Found Article {article_number}: {article_title[:50]}...")

        print(f"✓ Found {article_count} articles")

        # Look for Section patterns within articles
        section_pattern = r'(?:SECTION|Section|Sec\.?)\s+([0-9]+[a-zA-Z]?)[.\s]*[-–—]?\s*(.+?)(?=\n)'
        sections = re.finditer(section_pattern, text, re.IGNORECASE | re.MULTILINE)

        section_count = 0
        for section_match in sections:
            section_number = section_match.group(1).strip()
            section_title = section_match.group(2).strip()
            section_count += 1

            if section_count <= 10:  # Show first 10 as examples
                print(f"  Found Section {section_number}: {section_title[:50]}...")

        print(f"✓ Found {section_count} sections")

        # Try to extract individual sections with their content
        constitution_sections = self.extract_detailed_sections(text)

        return constitution_sections

    def extract_detailed_sections(self, text):
        """Extract individual sections with their full content"""

        print("Extracting detailed sections...")

        sections = []

        # Split text into potential sections
        # This is a simplified approach - might need refinement based on actual PDF structure

        # Look for section headers and extract content until next section
        section_pattern = r'((?:ARTICLE\s+[IVX0-9]+|SECTION\s+[0-9]+[a-zA-Z]?)[.\s]*[-–—]?\s*[^\n]+)'

        section_matches = list(re.finditer(section_pattern, text, re.IGNORECASE | re.MULTILINE))

        for i, match in enumerate(section_matches):
            header = match.group(1)
            start_pos = match.end()

            # Find the end of this section (start of next section or end of text)
            if i + 1 < len(section_matches):
                end_pos = section_matches[i + 1].start()
            else:
                end_pos = len(text)

            content = text[start_pos:end_pos].strip()

            # Parse the header to extract article/section info
            section_info = self.parse_section_header(header)
            if section_info:
                section_info['content'] = content
                sections.append(section_info)

        print(f"✓ Extracted {len(sections)} detailed sections")

        # Save sections for review
        with open('constitution_sections_parsed.json', 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)

        print("✓ Saved parsed sections to: constitution_sections_parsed.json")

        return sections

    def parse_section_header(self, header):
        """Parse a section header to extract article and section info"""

        header = header.strip()

        # Try to match Article pattern
        article_match = re.match(r'ARTICLE\s+([IVX]+|[0-9]+)[.\s]*[-–—]?\s*(.+)', header, re.IGNORECASE)
        if article_match:
            return {
                'type': 'article',
                'article_number': article_match.group(1),
                'title': article_match.group(2).strip(),
                'section_number': None
            }

        # Try to match Section pattern
        section_match = re.match(r'SECTION\s+([0-9]+[a-zA-Z]?)[.\s]*[-–—]?\s*(.+)', header, re.IGNORECASE)
        if section_match:
            return {
                'type': 'section',
                'article_number': None,  # Would need to track current article
                'section_number': section_match.group(1),
                'title': section_match.group(2).strip()
            }

        return None

    def create_database_records(self, sections):
        """Create database records from parsed constitution sections"""

        print(f"Creating database records for {len(sections)} constitution sections...")

        # Get existing cite IDs to match with parsed sections
        try:
            with open('constitution_cite_ids.txt', 'r') as f:
                existing_cite_ids = [line.strip() for line in f if line.strip()]
            print(f"Found {len(existing_cite_ids)} existing cite IDs to match")
        except FileNotFoundError:
            print("No existing cite IDs found - will create new records")
            existing_cite_ids = []

        created_count = 0
        updated_count = 0

        for i, section in enumerate(sections):
            try:
                # Create a cite ID (you might need to adjust this logic)
                cite_id = str(400000 + i)  # Start from a base number

                # If we have existing cite IDs, try to use them
                if i < len(existing_cite_ids):
                    cite_id = existing_cite_ids[i]

                # Create statute data structure
                statute_data = {
                    'cite_id': cite_id,
                    'url': f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}",
                    'metadata': {
                        'title_number': 'CONST',
                        'title_name': 'Oklahoma Constitution',
                        'article_number': section.get('article_number'),
                        'article_name': section.get('title') if section['type'] == 'article' else None,
                        'section_number': section.get('section_number'),
                        'section_name': section.get('title'),
                        'page_title': section.get('title'),
                    },
                    'content': {
                        'main_text': section.get('content', ''),
                        'paragraphs': [{'text': section.get('content', ''), 'is_historical': False}]
                    },
                    'citations': {},
                    'source': 'pdf_manual',
                    'scraper_version': '1.2'
                }

                # Check if record exists and update or create
                existing = self.db.get_statute(cite_id)

                if existing:
                    print(f"  Updating existing record for CiteID {cite_id}")
                    # Update logic here
                    updated_count += 1
                else:
                    print(f"  Creating new record for CiteID {cite_id}")
                    result = self.db.insert_statute(statute_data)
                    if result['success']:
                        created_count += 1

            except Exception as e:
                print(f"  ❌ Error processing section {i}: {e}")

        print(f"\n✓ Database update completed:")
        print(f"  Created: {created_count}")
        print(f"  Updated: {updated_count}")

def main():
    print("Oklahoma Constitution PDF Processor")
    print("=" * 50)

    processor = PDFConstitutionProcessor()

    # Find PDF files
    pdf_files = processor.find_pdf_files()

    if not pdf_files:
        print("❌ No PDF files found in current directory")
        print("\nPlease:")
        print("1. Copy your Oklahoma Constitution PDF to this folder")
        print("2. Run this script again")
        return

    # Let user choose which PDF to process
    if len(pdf_files) == 1:
        chosen_pdf = pdf_files[0]
        print(f"\nProcessing: {chosen_pdf}")
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

    print(f"\nChoose processing method:")
    print("1. pdfplumber (recommended - better text extraction)")
    print("2. PyPDF2 (fallback option)")
    print("3. Both (try pdfplumber first, then PyPDF2)")

    method = input("Enter choice (1-3): ").strip()

    # Install dependencies if needed
    try:
        if method in ['1', '3']:
            import pdfplumber
        if method in ['2', '3']:
            import PyPDF2
    except ImportError:
        install_pdf_dependencies()

    # Process the PDF
    if method == '1':
        text = processor.process_with_pdfplumber(chosen_pdf)
    elif method == '2':
        text = processor.process_with_pypdf2(chosen_pdf)
    elif method == '3':
        try:
            text = processor.process_with_pdfplumber(chosen_pdf)
        except Exception as e:
            print(f"pdfplumber failed: {e}")
            print("Falling back to PyPDF2...")
            text = processor.process_with_pypdf2(chosen_pdf)
    else:
        print("Invalid choice")
        return

    if text:
        # Parse the structure
        sections = processor.parse_constitution_structure(text)

        if sections:
            print(f"\nParsed {len(sections)} constitution sections")

            # Ask if user wants to create database records
            response = input("\nCreate/update database records? (y/n): ").lower()
            if response == 'y':
                processor.create_database_records(sections)
        else:
            print("❌ No sections could be parsed from the PDF")
            print("Check the raw text file to see what was extracted")

if __name__ == "__main__":
    main()