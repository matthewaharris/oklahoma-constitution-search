#!/usr/bin/env python3
"""
Slow HTML Downloader for Oklahoma Statutes
Downloads HTML files with respectful delays and resume capability
"""

import requests
import time
import json
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import hashlib

class SlowStatuteDownloader:
    def __init__(self, delay_seconds: int = 10, output_dir: str = 'statute_html'):
        """
        Initialize downloader

        Args:
            delay_seconds: Seconds between downloads (default 10)
            output_dir: Directory to save HTML files
        """
        self.delay = delay_seconds
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories for each title
        for title in range(1, 86):
            title_dir = self.output_dir / f"title_{title:02d}"
            title_dir.mkdir(exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Legal Research Tool - Contact: mharris26@gmail.com)'
        })

        # Progress tracking
        self.progress_file = 'download_progress.json'
        self.downloaded = self.load_progress()

    def load_progress(self) -> set:
        """Load list of already downloaded cite IDs"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('downloaded', []))
            except:
                return set()
        return set()

    def save_progress(self):
        """Save progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump({
                'downloaded': list(self.downloaded),
                'count': len(self.downloaded),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)

    def get_filename(self, cite_id: str, title_number: int) -> Path:
        """Generate filename for a statute"""
        title_dir = self.output_dir / f"title_{title_number:02d}"
        return title_dir / f"cite_{cite_id}.html"

    def download_statute(self, url: str, cite_id: str, title_number: int) -> bool:
        """Download a single statute HTML page"""

        # Skip if already downloaded
        if cite_id in self.downloaded:
            print(f"[SKIP] {cite_id} already downloaded")
            return True

        filename = self.get_filename(cite_id, title_number)

        # Check if file exists
        if filename.exists():
            print(f"[SKIP] {cite_id} file exists")
            self.downloaded.add(cite_id)
            return True

        print(f"Downloading cite_id: {cite_id}")
        print(f"  URL: {url}")
        print(f"  Waiting {self.delay} seconds...")
        time.sleep(self.delay)

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Save HTML
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)

            # Mark as downloaded
            self.downloaded.add(cite_id)

            # Save metadata
            meta_file = filename.with_suffix('.meta.json')
            with open(meta_file, 'w') as f:
                json.dump({
                    'cite_id': cite_id,
                    'url': url,
                    'title_number': title_number,
                    'downloaded_at': datetime.now().isoformat(),
                    'status_code': response.status_code,
                    'size_bytes': len(response.text)
                }, f, indent=2)

            print(f"[OK] Downloaded {cite_id} ({len(response.text)} bytes)")
            return True

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to download {cite_id}: {e}")
            return False

    def download_from_url_list(self, url_file: str = 'oklahoma_statute_urls.json'):
        """Download all statutes from a URL list file"""

        if not os.path.exists(url_file):
            print(f"[ERROR] URL file not found: {url_file}")
            print("Please run url_collector.py first!")
            return

        # Load URL list
        with open(url_file, 'r') as f:
            data = json.load(f)
            urls = data.get('urls', [])

        print("Oklahoma Statutes HTML Downloader")
        print(f"{'='*60}")
        print(f"Total statutes to download: {len(urls)}")
        print(f"Already downloaded: {len(self.downloaded)}")
        print(f"Remaining: {len(urls) - len(self.downloaded)}")
        print(f"Delay between requests: {self.delay} seconds")
        print(f"Estimated time: {(len(urls) - len(self.downloaded)) * self.delay / 3600:.1f} hours")
        print(f"{'='*60}\n")

        # Confirm before starting
        if len(urls) - len(self.downloaded) > 100:
            response = input("This will take a long time. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled")
                return

        # Download each statute
        success_count = 0
        failure_count = 0

        for i, statute_info in enumerate(urls, 1):
            cite_id = statute_info['cite_id']
            url = statute_info['url']
            title_number = statute_info['title_number']

            print(f"\n[{i}/{len(urls)}] Processing cite_id: {cite_id}")

            if self.download_statute(url, cite_id, title_number):
                success_count += 1
            else:
                failure_count += 1

            # Save progress every 10 downloads
            if i % 10 == 0:
                self.save_progress()
                print(f"\nProgress saved: {len(self.downloaded)} downloaded")

        # Final save
        self.save_progress()

        print(f"\n{'='*60}")
        print("Download Complete!")
        print(f"{'='*60}")
        print(f"Total processed: {len(urls)}")
        print(f"Successfully downloaded: {success_count}")
        print(f"Failed: {failure_count}")
        print(f"Already had: {len(self.downloaded) - success_count}")
        print(f"Output directory: {self.output_dir.absolute()}")

    def download_specific_titles(self, url_file: str, title_numbers: List[int]):
        """Download only specific titles"""

        with open(url_file, 'r') as f:
            data = json.load(f)
            urls = data.get('urls', [])

        # Filter to only requested titles
        filtered_urls = [u for u in urls if u['title_number'] in title_numbers]

        print(f"Downloading {len(filtered_urls)} statutes from titles: {title_numbers}")

        temp_file = 'temp_filtered_urls.json'
        with open(temp_file, 'w') as f:
            json.dump({'urls': filtered_urls}, f)

        self.download_from_url_list(temp_file)
        os.remove(temp_file)

    def get_stats(self) -> Dict:
        """Get download statistics"""
        stats = {
            'total_downloaded': len(self.downloaded),
            'by_title': {}
        }

        # Count by title
        for title in range(1, 86):
            title_dir = self.output_dir / f"title_{title:02d}"
            if title_dir.exists():
                html_files = list(title_dir.glob('*.html'))
                stats['by_title'][title] = len(html_files)

        return stats


def main():
    """Main entry point"""
    print("Oklahoma Statutes HTML Downloader")
    print()

    # Check if URL list exists
    if not os.path.exists('oklahoma_statute_urls.json'):
        print("[ERROR] URL list not found!")
        print("Please run url_collector.py first to collect statute URLs")
        return

    print("Options:")
    print("1. Download all statutes (WARNING: Takes many hours)")
    print("2. Download specific titles")
    print("3. Resume previous download")
    print("4. Show download statistics")
    print()

    choice = input("Enter choice (1-4): ").strip()

    downloader = SlowStatuteDownloader(delay_seconds=10)

    if choice == '1':
        # Download all
        downloader.download_from_url_list()

    elif choice == '2':
        # Specific titles
        titles_input = input("Enter title numbers (comma-separated, e.g., 1,2,3): ")
        titles = [int(t.strip()) for t in titles_input.split(',')]
        downloader.download_specific_titles('oklahoma_statute_urls.json', titles)

    elif choice == '3':
        # Resume
        print("Resuming previous download...")
        downloader.download_from_url_list()

    elif choice == '4':
        # Statistics
        stats = downloader.get_stats()
        print(f"\nDownload Statistics:")
        print(f"Total downloaded: {stats['total_downloaded']}")
        print(f"\nBy Title:")
        for title, count in sorted(stats['by_title'].items()):
            if count > 0:
                print(f"  Title {title}: {count} statutes")

    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        print("Progress has been saved. You can resume later.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
