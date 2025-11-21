#!/usr/bin/env python3
"""
Unified Statute Processor

Processes raw HTML files and uploads to BOTH:
1. Supabase (PostgreSQL) - for structured queries
2. Pinecone - for semantic search with embeddings

This combines the functionality of:
- upload_statutes_to_supabase.py
- html_processor.py

Usage:
    python process_statutes.py --title 10
    python process_statutes.py --title 11 --skip-embeddings  # Skip Pinecone
    python process_statutes.py --title 10 --supabase-only    # Only Supabase
    python process_statutes.py --title 10 --pinecone-only    # Only Pinecone
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict

# Import configurations
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import SUPABASE_URL, SUPABASE_KEY
else:
    try:
        from config import SUPABASE_URL, SUPABASE_KEY
    except ImportError:
        from config_production import SUPABASE_URL, SUPABASE_KEY

# Import clients
try:
    from supabase import create_client, Client
except ImportError:
    print("[ERROR] Supabase library not installed")
    print("Install with: pip install supabase")
    sys.exit(1)

from vector_database_builder import ConstitutionVectorBuilder

class UnifiedStatuteProcessor:
    def __init__(self, title_number: int, supabase_only: bool = False, pinecone_only: bool = False):
        self.title_number = title_number
        self.supabase_only = supabase_only
        self.pinecone_only = pinecone_only

        # Initialize Supabase
        if not pinecone_only:
            try:
                self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("[OK] Connected to Supabase")
            except Exception as e:
                print(f"[ERROR] Failed to connect to Supabase: {e}")
                if not pinecone_only:
                    sys.exit(1)

        # Initialize Pinecone
        if not supabase_only:
            try:
                self.builder = ConstitutionVectorBuilder()
                if not self.builder.setup_clients():
                    print("[ERROR] Failed to setup Pinecone client")
                    if not supabase_only:
                        sys.exit(1)

                index_name = f"oklahoma-statutes"
                self.builder.index = self.builder.pinecone_client.Index(index_name)
                print(f"[OK] Connected to Pinecone index: {index_name}")
            except Exception as e:
                print(f"[ERROR] Failed to connect to Pinecone: {e}")
                if not supabase_only:
                    sys.exit(1)

    def parse_html_file(self, html_path: Path, metadata: Dict) -> Dict:
        """Parse HTML file and extract statute data"""

        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')

        # Extract section name
        title_tag = soup.find('title')
        section_name = title_tag.get_text(strip=True) if title_tag else "Untitled"

        h1_tag = soup.find('h1')
        if h1_tag:
            section_name = h1_tag.get_text(strip=True)

        # Extract text
        main_content = soup.find('div', class_='main') or soup.find('div', id='content')
        if main_content:
            text_content = main_content.get_text(separator='\n', strip=True)
        else:
            paragraphs = soup.find_all('p')
            text_content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])

        # Clean text
        text_content = re.sub(r'\n{3,}', '\n\n', text_content).strip()

        # Extract section number
        section_match = re.search(r'Section\s+(\d+[A-Za-z]?[\-\d\.]*)', section_name, re.IGNORECASE)
        section_number = section_match.group(1) if section_match else ""

        cite_id = metadata.get('cite_id', html_path.stem.replace('cite_', ''))

        return {
            'cite_id': cite_id,
            'url': metadata.get('url', ''),
            'title_number': str(self.title_number),
            'section_number': section_number,
            'section_name': section_name,
            'text': text_content,
            'downloaded_at': metadata.get('downloaded_at', ''),
            'processed_at': datetime.now().isoformat()
        }

    def upload_to_supabase(self, records: List[Dict]) -> bool:
        """Upload batch to Supabase"""
        if self.pinecone_only:
            return True

        try:
            # Prepare for Supabase schema
            supabase_records = []
            for record in records:
                supabase_record = {
                    'cite_id': record['cite_id'],
                    'url': record['url'],
                    'title_number': record['title_number'],
                    'title_name': f"Title {self.title_number}",
                    'chapter_number': None,
                    'chapter_name': None,
                    'article_number': None,
                    'article_name': None,
                    'section_number': record['section_number'],
                    'section_name': record['section_name'],
                    'page_title': record['section_name'],
                    'title_bar': None,
                    'citation_format': None,
                    'main_text': record['text'],
                    'full_json': {
                        'cite_id': record['cite_id'],
                        'title_number': self.title_number,
                        'section_name': record['section_name'],
                        'section_number': record['section_number'],
                        'text': record['text'],
                        'url': record['url'],
                        'downloaded_at': record['downloaded_at'],
                        'processed_at': record['processed_at']
                    },
                    'scraper_version': '1.0'
                }
                supabase_records.append(supabase_record)

            result = self.supabase.table('statutes').insert(supabase_records).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Supabase upload failed: {e}")
            return False

    def upload_to_pinecone(self, records: List[Dict]) -> bool:
        """Upload batch to Pinecone with embeddings"""
        if self.supabase_only:
            return True

        try:
            # Create embeddings
            texts = [f"{r['section_name']}\n\n{r['text']}" for r in records]
            embeddings = self.builder.create_embeddings(texts)

            if not embeddings:
                print(f"[ERROR] Failed to create embeddings")
                return False

            # Prepare vectors for Pinecone
            vectors = []
            for record, embedding in zip(records, embeddings):
                vector = {
                    'id': f"statute_{record['cite_id']}",
                    'values': embedding,
                    'metadata': {
                        'cite_id': record['cite_id'],
                        'title_number': self.title_number,
                        'section_name': record['section_name'][:500],
                        'section_number': record['section_number'],
                        'text': record['text'][:10000],
                        'type': 'statute'
                    }
                }
                vectors.append(vector)

            # Upload to Pinecone
            self.builder.index.upsert(vectors=vectors)
            return True
        except Exception as e:
            print(f"[ERROR] Pinecone upload failed: {e}")
            return False

    def process_title(self, batch_size: int = 50):
        """Process all HTML files for a title"""

        html_dir = Path(f'statute_html/title_{self.title_number}')

        if not html_dir.exists():
            print(f"[ERROR] Directory not found: {html_dir}")
            return

        html_files = list(html_dir.glob('*.html'))
        print(f"\nFound {len(html_files)} HTML files to process")
        print()

        success_count = 0
        failure_count = 0
        batch = []

        for i, html_path in enumerate(html_files, 1):
            try:
                # Load metadata
                meta_path = html_path.with_suffix('.meta.json')
                metadata = {}
                if meta_path.exists():
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)

                # Parse HTML
                record = self.parse_html_file(html_path, metadata)
                batch.append(record)

                # Upload batch when full
                if len(batch) >= batch_size:
                    supabase_ok = self.upload_to_supabase(batch)
                    pinecone_ok = self.upload_to_pinecone(batch)

                    if supabase_ok or pinecone_ok:
                        success_count += len(batch)

                        uploads = []
                        if not self.pinecone_only:
                            uploads.append("Supabase")
                        if not self.supabase_only:
                            uploads.append("Pinecone")

                        print(f"[{i}/{len(html_files)}] Uploaded batch of {len(batch)} to {' & '.join(uploads)}")
                    else:
                        failure_count += len(batch)

                    batch = []

            except Exception as e:
                print(f"[ERROR] Failed to process {html_path.name}: {e}")
                failure_count += 1

        # Upload remaining batch
        if batch:
            supabase_ok = self.upload_to_supabase(batch)
            pinecone_ok = self.upload_to_pinecone(batch)

            if supabase_ok or pinecone_ok:
                success_count += len(batch)

                uploads = []
                if not self.pinecone_only:
                    uploads.append("Supabase")
                if not self.supabase_only:
                    uploads.append("Pinecone")

                print(f"Uploaded final batch of {len(batch)} to {' & '.join(uploads)}")
            else:
                failure_count += len(batch)

        print("\n" + "=" * 60)
        print("Processing Complete!")
        print("=" * 60)
        print(f"Successfully processed: {success_count}")
        print(f"Failed: {failure_count}")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Process statute HTML files to Supabase and Pinecone')
    parser.add_argument('--title', type=int, required=True, help='Title number (e.g., 10)')
    parser.add_argument('--supabase-only', action='store_true', help='Only upload to Supabase')
    parser.add_argument('--pinecone-only', action='store_true', help='Only upload to Pinecone')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for uploads')

    args = parser.parse_args()

    if args.supabase_only and args.pinecone_only:
        print("[ERROR] Cannot specify both --supabase-only and --pinecone-only")
        sys.exit(1)

    print("=" * 60)
    print(f"Processing Title {args.title} Statutes")
    print("=" * 60)

    targets = []
    if not args.pinecone_only:
        targets.append("Supabase (PostgreSQL)")
    if not args.supabase_only:
        targets.append("Pinecone (Vector DB)")

    print(f"Targets: {' & '.join(targets)}")
    print("=" * 60)
    print()

    processor = UnifiedStatuteProcessor(
        title_number=args.title,
        supabase_only=args.supabase_only,
        pinecone_only=args.pinecone_only
    )

    processor.process_title(batch_size=args.batch_size)

if __name__ == "__main__":
    main()
