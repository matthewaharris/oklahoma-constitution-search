#!/usr/bin/env python3
"""
HTML Processor for Oklahoma Statutes
Processes downloaded HTML files and loads them into Pinecone + Supabase
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Import our existing tools
from vector_database_builder import ConstitutionVectorBuilder

class StatuteHTMLProcessor:
    def __init__(self, html_dir: str = 'statute_html'):
        """
        Initialize HTML processor

        Args:
            html_dir: Directory containing downloaded HTML files
        """
        self.html_dir = Path(html_dir)
        self.builder = ConstitutionVectorBuilder()
        self.processed = self.load_processed()
        self.processed_file = 'processing_progress.json'

    def load_processed(self) -> set:
        """Load list of already processed cite IDs"""
        if os.path.exists('processing_progress.json'):
            try:
                with open('processing_progress.json', 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed', []))
            except:
                return set()
        return set()

    def save_processed(self):
        """Save processing progress"""
        with open('processing_progress.json', 'w') as f:
            json.dump({
                'processed': list(self.processed),
                'count': len(self.processed),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)

    def parse_statute_html(self, html_path: Path) -> Optional[Dict]:
        """
        Parse a statute HTML file and extract structured data

        Returns:
            Dictionary with statute data or None if parsing fails
        """
        try:
            # Read HTML file
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()

            soup = BeautifulSoup(html, 'html.parser')

            # Load metadata file
            meta_path = html_path.with_suffix('.meta.json')
            metadata = {}
            if meta_path.exists():
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)

            # Extract statute title (usually in <title> or first <h1>/<h2>)
            title_tag = soup.find('title')
            section_name = title_tag.get_text(strip=True) if title_tag else "Untitled Section"

            # Try to find section name in main content
            h1_tag = soup.find('h1')
            if h1_tag:
                section_name = h1_tag.get_text(strip=True)

            # Extract statute text
            # OSCN typically puts statute text in specific divs or paragraphs
            # This may need adjustment based on actual HTML structure
            text_content = ""

            # Look for main content area
            main_content = soup.find('div', class_='main') or soup.find('div', id='content')
            if main_content:
                # Get all text, clean up whitespace
                text_content = main_content.get_text(separator='\n', strip=True)
            else:
                # Fallback: get all paragraph text
                paragraphs = soup.find_all('p')
                text_content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])

            # Clean up text
            text_content = re.sub(r'\n{3,}', '\n\n', text_content)  # Max 2 newlines
            text_content = text_content.strip()

            if not text_content or len(text_content) < 50:
                print(f"[WARNING] {html_path.name}: Content too short ({len(text_content)} chars)")
                return None

            # Extract section number from title or filename
            section_match = re.search(r'Section\s+(\d+[A-Za-z]?[\-\d\.]*)', section_name, re.IGNORECASE)
            section_number = section_match.group(1) if section_match else ""

            # Extract title number from metadata or filename
            title_number = metadata.get('title_number', 0)
            if not title_number:
                # Try to extract from filename (e.g., title_01/cite_123.html)
                title_match = re.search(r'title_(\d+)', str(html_path))
                title_number = int(title_match.group(1)) if title_match else 0

            # Build structured record
            record = {
                'cite_id': metadata.get('cite_id', html_path.stem.replace('cite_', '')),
                'title_number': title_number,
                'section_number': section_number,
                'section_name': section_name,
                'text': text_content,
                'url': metadata.get('url', ''),
                'downloaded_at': metadata.get('downloaded_at', ''),
                'processed_at': datetime.now().isoformat()
            }

            return record

        except Exception as e:
            print(f"[ERROR] Failed to parse {html_path}: {e}")
            return None

    def process_all_html_files(self, start_title: Optional[int] = None, end_title: Optional[int] = None):
        """
        Process all HTML files and upload to databases

        Args:
            start_title: Optional starting title number (1-85)
            end_title: Optional ending title number (1-85)
        """
        print("Oklahoma Statutes HTML Processor")
        print("=" * 60)
        print(f"HTML directory: {self.html_dir.absolute()}")
        print(f"Already processed: {len(self.processed)}")

        # Initialize vector builder
        print("\nInitializing Pinecone and OpenAI...")
        if not self.builder.setup_clients():
            print("[ERROR] Failed to setup clients")
            return

        # Connect to index
        try:
            self.builder.index = self.builder.pinecone_client.Index("oklahoma-statutes")
            print(f"[OK] Connected to Pinecone index")
        except Exception as e:
            print(f"[ERROR] Failed to connect to index: {e}")
            print("You may need to create the index first:")
            print("  python -c \"from vector_database_builder import *; create_statute_index()\"")
            return

        # Find all HTML files
        html_files = []
        for title_dir in sorted(self.html_dir.glob('title_*')):
            if not title_dir.is_dir():
                continue

            # Check if within title range
            title_num = int(title_dir.name.replace('title_', ''))
            if start_title and title_num < start_title:
                continue
            if end_title and title_num > end_title:
                continue

            html_files.extend(sorted(title_dir.glob('*.html')))

        total_files = len(html_files)
        print(f"\nFound {total_files} HTML files to process")

        if total_files == 0:
            print("[ERROR] No HTML files found!")
            print("Make sure you've run slow_downloader.py first")
            return

        # Confirm before processing
        if total_files > 100:
            response = input(f"\nThis will process {total_files} files. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled")
                return

        # Process files
        success_count = 0
        failure_count = 0
        skipped_count = 0

        records_batch = []
        batch_size = 50  # Process in batches

        for i, html_path in enumerate(html_files, 1):
            cite_id = html_path.stem.replace('cite_', '')

            # Skip if already processed
            if cite_id in self.processed:
                skipped_count += 1
                if i % 100 == 0:
                    print(f"[{i}/{total_files}] Skipped {cite_id} (already processed)")
                continue

            print(f"\n[{i}/{total_files}] Processing {html_path.name}...")

            # Parse HTML
            record = self.parse_statute_html(html_path)

            if not record:
                failure_count += 1
                continue

            records_batch.append(record)

            # Upload batch when full
            if len(records_batch) >= batch_size:
                if self.upload_batch(records_batch):
                    success_count += len(records_batch)
                    for r in records_batch:
                        self.processed.add(r['cite_id'])
                else:
                    failure_count += len(records_batch)

                records_batch = []
                self.save_processed()
                print(f"Progress saved: {len(self.processed)} processed")

        # Upload remaining records
        if records_batch:
            if self.upload_batch(records_batch):
                success_count += len(records_batch)
                for r in records_batch:
                    self.processed.add(r['cite_id'])
            else:
                failure_count += len(records_batch)

            self.save_processed()

        # Final summary
        print("\n" + "=" * 60)
        print("Processing Complete!")
        print("=" * 60)
        print(f"Total files: {total_files}")
        print(f"Successfully processed: {success_count}")
        print(f"Failed: {failure_count}")
        print(f"Skipped (already done): {skipped_count}")
        print(f"Total in database: {len(self.processed)}")

    def upload_batch(self, records: List[Dict]) -> bool:
        """
        Upload a batch of records to Pinecone

        Args:
            records: List of statute records

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"  Generating embeddings for {len(records)} records...")

            # Create embeddings
            texts = [f"{r['section_name']}\n\n{r['text']}" for r in records]
            embeddings = self.builder.create_embeddings(texts)

            if not embeddings or len(embeddings) != len(records):
                print(f"[ERROR] Embedding generation failed")
                return False

            # Prepare vectors for Pinecone
            vectors = []
            for record, embedding in zip(records, embeddings):
                vector = {
                    'id': f"statute_{record['cite_id']}",
                    'values': embedding,
                    'metadata': {
                        'cite_id': record['cite_id'],
                        'title_number': record['title_number'],
                        'section_number': record['section_number'],
                        'section_name': record['section_name'][:500],  # Limit length
                        'text': record['text'][:10000],  # Pinecone metadata limit
                        'url': record['url'],
                        'type': 'statute'
                    }
                }
                vectors.append(vector)

            # Upload to Pinecone
            print(f"  Uploading {len(vectors)} vectors to Pinecone...")
            self.builder.index.upsert(vectors=vectors)

            print(f"[OK] Uploaded {len(vectors)} statutes")
            return True

        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            return False


def create_statute_index():
    """Helper function to create the statute index"""
    from vector_database_builder import ConstitutionVectorBuilder

    builder = ConstitutionVectorBuilder()
    if not builder.setup_clients():
        print("[ERROR] Failed to setup clients")
        return

    print("Creating Oklahoma Statutes index...")
    print("This may take a minute...")

    try:
        # Create serverless index for statutes
        from pinecone import ServerlessSpec

        builder.pinecone_client.create_index(
            name="oklahoma-statutes",
            dimension=1536,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )

        print("[OK] Index created successfully!")
        print("You can now run the HTML processor")

    except Exception as e:
        if "already exists" in str(e).lower():
            print("[OK] Index already exists")
        else:
            print(f"[ERROR] Failed to create index: {e}")


def main():
    """Main entry point"""
    print("Oklahoma Statutes HTML Processor")
    print()

    # Check if HTML directory exists
    if not os.path.exists('statute_html'):
        print("[ERROR] statute_html directory not found!")
        print("Please run slow_downloader.py first to download HTML files")
        return

    print("Options:")
    print("1. Process all statutes")
    print("2. Process specific title range")
    print("3. Resume previous processing")
    print("4. Create statute index (run this first if index doesn't exist)")
    print("5. Show processing statistics")
    print()

    choice = input("Enter choice (1-5): ").strip()

    if choice == '1':
        # Process all
        processor = StatuteHTMLProcessor()
        processor.process_all_html_files()

    elif choice == '2':
        # Specific range
        start = int(input("Start title (1-85): ").strip())
        end = int(input("End title (1-85): ").strip())
        processor = StatuteHTMLProcessor()
        processor.process_all_html_files(start_title=start, end_title=end)

    elif choice == '3':
        # Resume
        print("Resuming previous processing...")
        processor = StatuteHTMLProcessor()
        processor.process_all_html_files()

    elif choice == '4':
        # Create index
        create_statute_index()

    elif choice == '5':
        # Statistics
        processor = StatuteHTMLProcessor()
        print(f"\nProcessing Statistics:")
        print(f"Total processed: {len(processor.processed)}")

        # Count HTML files
        html_files = list(Path('statute_html').rglob('*.html'))
        print(f"Total HTML files: {len(html_files)}")
        print(f"Remaining: {len(html_files) - len(processor.processed)}")

        # By title
        title_counts = {}
        for html_file in html_files:
            title_match = re.search(r'title_(\d+)', str(html_file))
            if title_match:
                title_num = int(title_match.group(1))
                title_counts[title_num] = title_counts.get(title_num, 0) + 1

        print(f"\nFiles by Title:")
        for title, count in sorted(title_counts.items()):
            print(f"  Title {title}: {count} files")

    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
        print("Progress has been saved. You can resume later.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
