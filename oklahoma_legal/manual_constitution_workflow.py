#!/usr/bin/env python3
"""
Manual Constitution Workflow
1. Generate URLs for manual download
2. Process downloaded HTML files
3. Update database with proper data
"""

import json
import os
import glob
from pathlib import Path
from bs4 import BeautifulSoup
import re
from supabase_client import StatutesDatabase

class ManualConstitutionProcessor:
    def __init__(self):
        self.db = StatutesDatabase()

    def generate_download_urls(self):
        """Generate all the URLs you need to manually save"""

        # Get cite IDs from your previous scraping
        cite_ids = []

        # Try to load from previous results
        try:
            with open('constitution_cite_ids.txt', 'r') as f:
                cite_ids = [line.strip() for line in f if line.strip()]
            print(f"✓ Loaded {len(cite_ids)} cite IDs from constitution_cite_ids.txt")
        except FileNotFoundError:
            print("❌ constitution_cite_ids.txt not found")
            return

        # Generate URLs and save instructions
        urls = []
        for cite_id in cite_ids:
            url = f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}"
            urls.append({
                'cite_id': cite_id,
                'url': url,
                'filename': f"constitution_{cite_id}.html"
            })

        # Save URL list
        with open('constitution_urls_to_download.json', 'w', encoding='utf-8') as f:
            json.dump(urls, f, indent=2)

        # Create download instructions
        instructions = f"""
MANUAL DOWNLOAD INSTRUCTIONS
============================

You need to manually save {len(cite_ids)} constitution sections.

RECOMMENDED APPROACH:
1. Create a folder called 'constitution_html' in this directory
2. Open each URL below in your browser
3. Right-click → Save as → Save with the exact filename shown

BATCH DOWNLOAD TIPS:
- Use browser bookmarks for efficiency
- Save 10-20 at a time to avoid overwhelming yourself
- Use the filename pattern: constitution_[CITE_ID].html
- All files should go in the 'constitution_html' folder

URLs TO DOWNLOAD:
"""

        # Add first 10 URLs as examples
        for i, url_info in enumerate(urls[:10]):
            instructions += f"""
{i+1:3d}. URL: {url_info['url']}
     Save as: constitution_html/{url_info['filename']}
"""

        if len(urls) > 10:
            instructions += f"""
... and {len(urls) - 10} more URLs (see constitution_urls_to_download.json for complete list)

AUTOMATION OPTION:
If you want to try automated downloading with browser automation:
- Install: pip install selenium
- Run: python auto_download_constitution.py
"""

        # Save instructions
        with open('DOWNLOAD_INSTRUCTIONS.txt', 'w', encoding='utf-8') as f:
            f.write(instructions)

        print(f"✓ Generated {len(urls)} URLs for manual download")
        print(f"✓ Instructions saved to: DOWNLOAD_INSTRUCTIONS.txt")
        print(f"✓ Full URL list saved to: constitution_urls_to_download.json")

        return urls

    def create_download_folder(self):
        """Create the folder for HTML downloads"""
        folder = Path('constitution_html')
        folder.mkdir(exist_ok=True)
        print(f"✓ Created folder: {folder}")
        return folder

    def process_downloaded_files(self):
        """Process all manually downloaded HTML files"""

        html_folder = Path('constitution_html')
        if not html_folder.exists():
            print(f"❌ Folder {html_folder} not found!")
            print("Create the folder and download HTML files first.")
            return

        # Find all HTML files
        html_files = list(html_folder.glob('*.html'))

        if not html_files:
            print(f"❌ No HTML files found in {html_folder}")
            return

        print(f"Found {len(html_files)} HTML files to process")

        processed_count = 0
        updated_count = 0
        errors = []

        for html_file in html_files:
            try:
                # Extract cite ID from filename
                cite_id_match = re.search(r'constitution_(\d+)\.html', html_file.name)
                if not cite_id_match:
                    print(f"⚠️ Skipping {html_file.name} - can't extract cite ID")
                    continue

                cite_id = cite_id_match.group(1)

                print(f"Processing CiteID {cite_id}...")

                # Parse the HTML file
                statute_data = self.parse_constitution_html(html_file, cite_id)

                if statute_data:
                    # Update the database
                    success = self.update_database_record(cite_id, statute_data)
                    if success:
                        updated_count += 1
                        print(f"  ✓ Updated database for {cite_id}")
                    else:
                        print(f"  ❌ Failed to update database for {cite_id}")

                processed_count += 1

            except Exception as e:
                error_msg = f"Error processing {html_file.name}: {e}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")

        print(f"\n" + "="*50)
        print(f"PROCESSING COMPLETED")
        print(f"="*50)
        print(f"Files processed: {processed_count}")
        print(f"Database records updated: {updated_count}")
        print(f"Errors: {len(errors)}")

        if errors:
            print(f"\nErrors encountered:")
            for error in errors[:5]:  # Show first 5
                print(f"  {error}")

        # Save processing results
        results = {
            'processed_count': processed_count,
            'updated_count': updated_count,
            'errors': errors
        }

        with open('manual_processing_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nResults saved to: manual_processing_results.json")

    def parse_constitution_html(self, html_file, cite_id):
        """Parse a single HTML file to extract constitution data"""

        # Try multiple encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        html_content = None

        for encoding in encodings:
            try:
                with open(html_file, 'r', encoding=encoding) as f:
                    html_content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if html_content is None:
            print(f"  ❌ Could not decode {html_file}")
            return None

        # Check if this is a Cloudflare/Turnstile page
        if ('turnstile' in html_content.lower() or
            'cloudflare' in html_content.lower() or
            'just a moment' in html_content.lower()):
            print(f"  ⚠️ {cite_id} appears to be a Cloudflare challenge page")
            return None

        soup = BeautifulSoup(html_content, 'html.parser')

        # Use our existing scraper logic to parse
        from final_oklahoma_scraper import FinalOklahomaStatutesScraper
        scraper = FinalOklahomaStatutesScraper()

        # Extract data using existing methods
        try:
            metadata = scraper.extract_statute_metadata(soup)
            content = scraper.extract_statute_content(soup)
            citations = scraper.extract_citations_and_references(soup)

            # Build the statute data structure
            statute_data = {
                'cite_id': cite_id,
                'url': f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}",
                'metadata': metadata,
                'content': content,
                'citations': citations,
                'source': 'manual_html',
                'scraper_version': '1.1'
            }

            return statute_data

        except Exception as e:
            print(f"  ❌ Error parsing {cite_id}: {e}")
            return None

    def update_database_record(self, cite_id, statute_data):
        """Update existing database record with proper data"""

        try:
            # Check if record exists
            existing = self.db.get_statute(cite_id)

            if not existing:
                print(f"  ⚠️ No existing record for {cite_id} - inserting new")
                result = self.db.insert_statute(statute_data)
                return result['success']

            # Update the existing record
            statute_id = existing['id']

            # Prepare update data
            update_data = {
                'title_number': statute_data['metadata'].get('title_number'),
                'title_name': statute_data['metadata'].get('title_name'),
                'chapter_number': statute_data['metadata'].get('chapter_number'),
                'chapter_name': statute_data['metadata'].get('chapter_name'),
                'article_number': statute_data['metadata'].get('article_number'),
                'article_name': statute_data['metadata'].get('article_name'),
                'section_number': statute_data['metadata'].get('section_number'),
                'section_name': statute_data['metadata'].get('section_name'),
                'page_title': statute_data['metadata'].get('page_title'),
                'title_bar': statute_data['metadata'].get('title_bar'),
                'citation_format': statute_data['metadata'].get('citation_format'),
                'main_text': statute_data['content'].get('main_text'),
                'full_json': statute_data,
                'scraper_version': '1.1_manual'
            }

            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}

            # Update the record
            result = self.db.client.table('statutes').update(update_data).eq('id', statute_id).execute()

            if result.data:
                # Update related tables if needed
                self._update_related_tables(statute_id, statute_data)
                return True
            else:
                print(f"  ❌ Update failed for {cite_id}")
                return False

        except Exception as e:
            print(f"  ❌ Database update error for {cite_id}: {e}")
            return False

    def _update_related_tables(self, statute_id, statute_data):
        """Update paragraphs, definitions, etc. for manually processed statute"""

        try:
            # Clear existing related data
            self.db.client.table('statute_paragraphs').delete().eq('statute_id', statute_id).execute()
            self.db.client.table('statute_definitions').delete().eq('statute_id', statute_id).execute()

            # Insert new data
            if 'paragraphs' in statute_data['content']:
                self.db._insert_paragraphs(statute_id, statute_data['content']['paragraphs'])

            if 'definitions' in statute_data['content']:
                self.db._insert_definitions(statute_id, statute_data['content']['definitions'])

        except Exception as e:
            print(f"    Warning: Error updating related tables: {e}")

def main():
    print("Manual Constitution Processing Workflow")
    print("=" * 50)

    processor = ManualConstitutionProcessor()

    print("Choose an option:")
    print("1. Generate download URLs and instructions")
    print("2. Process downloaded HTML files")
    print("3. Both (generate URLs then process existing files)")
    print("4. Exit")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == '1':
        processor.create_download_folder()
        urls = processor.generate_download_urls()
        if urls:
            print(f"\nNext steps:")
            print(f"1. Read DOWNLOAD_INSTRUCTIONS.txt")
            print(f"2. Download the {len(urls)} HTML files")
            print(f"3. Run this script again and choose option 2")

    elif choice == '2':
        processor.process_downloaded_files()

    elif choice == '3':
        processor.create_download_folder()
        urls = processor.generate_download_urls()
        if urls:
            print(f"\nDownload instructions generated.")
            print("Processing any existing HTML files...")
            processor.process_downloaded_files()

    elif choice == '4':
        print("Goodbye!")

    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()