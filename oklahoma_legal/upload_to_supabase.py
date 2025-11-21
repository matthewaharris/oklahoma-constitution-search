"""
Upload Oklahoma legal documents to Supabase
Handles both Constitution and Statutes with progress tracking and resume capability
"""

import os
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from supabase import create_client, Client
from oklahoma_document_parser import OklahomaDocumentParser

# Load credentials
try:
    import config
    SUPABASE_URL = config.SUPABASE_URL
    SUPABASE_KEY = config.SUPABASE_KEY
except ImportError:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Configuration
BATCH_SIZE = 50  # Upload 50 records at a time
PROGRESS_FILE = "supabase_upload_progress.json"

class SupabaseUploader:
    """Upload parsed documents to Supabase with progress tracking"""

    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.parser = OklahomaDocumentParser()
        self.progress = self._load_progress()

    def _load_progress(self) -> Dict:
        """Load progress from file"""
        if Path(PROGRESS_FILE).exists():
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        return {'uploaded': [], 'failed': []}

    def _save_progress(self):
        """Save progress to file"""
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def _prepare_record(self, parsed_data: Dict) -> Dict:
        """Prepare a record for Supabase insertion"""
        # Map parsed data to database schema
        record = {
            'cite_id': parsed_data['cite_id'],
            'url': parsed_data['url'],
            'page_title': parsed_data.get('page_title'),
            'citation_format': parsed_data.get('citation_format'),
            'main_text': parsed_data.get('main_text'),
            'scraped_at': parsed_data.get('scraped_at'),
            'scraper_version': parsed_data.get('scraper_version'),
        }

        # Add document-type specific fields
        doc_type = parsed_data.get('document_type', 'statute')

        # Try to add document_type if column exists
        try:
            record['document_type'] = doc_type
        except:
            pass

        if doc_type == 'constitution':
            record.update({
                'article_number': parsed_data.get('article_number'),
                'article_name': parsed_data.get('article_name'),
                'section_number': parsed_data.get('section_number'),
                'section_name': parsed_data.get('section_name'),
            })
        else:  # statute
            record.update({
                'title_number': parsed_data.get('title_number'),
                'title_name': parsed_data.get('title_name'),
                'chapter_number': parsed_data.get('chapter_number'),
                'chapter_name': parsed_data.get('chapter_name'),
                'section_number': parsed_data.get('section_number'),
                'section_name': parsed_data.get('section_name'),
            })

        # Remove None values to avoid issues
        return {k: v for k, v in record.items() if v is not None}

    def upload_file(self, html_file: Path) -> bool:
        """
        Parse and upload a single HTML file

        Returns:
            True if successful, False otherwise
        """
        try:
            cite_id = html_file.stem.replace('CiteID_', '')

            # Skip if already uploaded
            if cite_id in self.progress['uploaded']:
                return True

            # Parse the file
            parsed_data = self.parser.parse_html_file(html_file)

            # Prepare record
            record = self._prepare_record(parsed_data)

            # Upload to Supabase
            self.supabase.table('statutes').upsert(record).execute()

            # Track success
            self.progress['uploaded'].append(cite_id)
            return True

        except Exception as e:
            # Track failure
            self.progress['failed'].append({
                'cite_id': cite_id if 'cite_id' in locals() else html_file.stem,
                'file': str(html_file),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return False

    def upload_batch(self, html_files: List[Path]) -> tuple:
        """
        Upload a batch of files

        Returns:
            (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0

        for html_file in html_files:
            if self.upload_file(html_file):
                success_count += 1
            else:
                failure_count += 1

        # Save progress after each batch
        self._save_progress()

        return success_count, failure_count

    def upload_directory(self, directory: Path, document_type: str):
        """
        Upload all HTML files from a directory

        Args:
            directory: Path to directory containing HTML files
            document_type: 'constitution' or 'statutes'
        """
        # Get all HTML files
        if document_type == 'statutes':
            # Recursively get all HTML files from title subdirectories
            html_files = list(directory.rglob('*.html'))
        else:
            # Get files directly from constitution directory
            html_files = list(directory.glob('*.html'))

        total_files = len(html_files)
        print(f"\nFound {total_files:,} files to upload from {directory}")

        # Process in batches
        batch = []
        uploaded_count = 0
        failed_count = 0

        for i, html_file in enumerate(html_files, 1):
            batch.append(html_file)

            # Process batch when it reaches BATCH_SIZE or at the end
            if len(batch) >= BATCH_SIZE or i == total_files:
                success, failures = self.upload_batch(batch)
                uploaded_count += success
                failed_count += failures

                # Progress update
                progress_pct = (i / total_files) * 100
                print(f"Progress: {i:,}/{total_files:,} ({progress_pct:.1f}%) | "
                      f"Uploaded: {uploaded_count:,} | Failed: {failed_count}")

                batch = []

        return uploaded_count, failed_count


def main():
    """Main upload function"""
    print("=" * 70)
    print("OKLAHOMA LEGAL DOCUMENTS - SUPABASE UPLOAD")
    print("=" * 70)

    uploader = SupabaseUploader()

    # Check if we have previous progress
    if uploader.progress['uploaded']:
        print(f"\nResuming from previous upload:")
        print(f"  Already uploaded: {len(uploader.progress['uploaded']):,} documents")
        print(f"  Previous failures: {len(uploader.progress['failed'])}")

    # Upload Constitution first (smaller dataset)
    print("\n" + "=" * 70)
    print("UPLOADING OKLAHOMA CONSTITUTION")
    print("=" * 70)

    const_dir = Path("html_files/constitution")
    const_success, const_failed = uploader.upload_directory(const_dir, 'constitution')

    print(f"\nConstitution Upload Complete:")
    print(f"  Success: {const_success:,}")
    print(f"  Failed: {const_failed}")

    # Upload Statutes
    print("\n" + "=" * 70)
    print("UPLOADING OKLAHOMA STATUTES")
    print("=" * 70)

    stat_dir = Path("html_files/statutes")
    stat_success, stat_failed = uploader.upload_directory(stat_dir, 'statutes')

    print(f"\nStatutes Upload Complete:")
    print(f"  Success: {stat_success:,}")
    print(f"  Failed: {stat_failed}")

    # Final summary
    print("\n" + "=" * 70)
    print("UPLOAD SUMMARY")
    print("=" * 70)
    print(f"Total uploaded: {const_success + stat_success:,}")
    print(f"Total failed: {const_failed + stat_failed}")
    print(f"\nSuccess rate: {((const_success + stat_success) / 50094 * 100):.2f}%")

    if uploader.progress['failed']:
        print(f"\nFailed uploads saved to: {PROGRESS_FILE}")
        print("You can retry failed uploads later.")

    print("\nDone!")


if __name__ == "__main__":
    main()
