#!/usr/bin/env python3
"""
Oklahoma Legal Documents HTML Downloader
Downloads HTML files from collected URLs with respectful delays and resume capability
"""

import requests
import time
import json
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import sys

class HTMLDownloader:
    def __init__(self, delay_seconds: int = 2):
        """
        Initialize HTML downloader

        Args:
            delay_seconds: Seconds to wait between requests (default 10)
        """
        self.delay = delay_seconds
        self.base_url = "https://www.oscn.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Legal Research Tool - Contact: mharris26@gmail.com)'
        })

        # Progress tracking
        self.progress_file = None
        self.downloaded_ids = set()
        self.failed_ids = []

    def load_urls(self, url_file: str) -> List[Dict]:
        """Load URLs from JSON file"""
        print(f"Loading URLs from {url_file}...")

        if not os.path.exists(url_file):
            print(f"[ERROR] URL file not found: {url_file}")
            return []

        with open(url_file, 'r') as f:
            data = json.load(f)

        urls = data.get('urls', [])
        print(f"[OK] Loaded {len(urls)} URLs")
        return urls

    def load_progress(self, progress_file: str):
        """Load progress from previous run"""
        self.progress_file = progress_file

        if os.path.exists(progress_file):
            print(f"Loading progress from {progress_file}...")
            with open(progress_file, 'r') as f:
                progress = json.load(f)

            self.downloaded_ids = set(progress.get('downloaded', []))
            self.failed_ids = progress.get('failed', [])

            print(f"[OK] Resuming from previous run")
            print(f"    Already downloaded: {len(self.downloaded_ids)} files")
            print(f"    Previously failed: {len(self.failed_ids)} files")
        else:
            print(f"Starting fresh download (no progress file found)")

    def save_progress(self):
        """Save current progress"""
        if self.progress_file:
            progress = {
                'downloaded': list(self.downloaded_ids),
                'failed': self.failed_ids,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)

    def download_html(self, url: str, cite_id: str, output_path: str) -> bool:
        """
        Download single HTML file

        Args:
            url: URL to download
            cite_id: Citation ID for the document
            output_path: Path to save HTML file

        Returns:
            True if successful, False otherwise
        """
        # Check if already downloaded
        if cite_id in self.downloaded_ids:
            return True

        print(f"Downloading CiteID {cite_id}...")
        print(f"  URL: {url}")
        print(f"  Waiting {self.delay} seconds...")
        time.sleep(self.delay)

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Save HTML to file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Try multiple encodings to save the HTML
            for encoding in ['windows-1252', 'utf-8', 'latin-1']:
                try:
                    with open(output_path, 'w', encoding=encoding) as f:
                        f.write(response.text)
                    break
                except UnicodeEncodeError:
                    continue
            else:
                # If all encodings fail, save as bytes
                with open(output_path, 'wb') as f:
                    f.write(response.content)

            print(f"[OK] Saved to {output_path}")

            # Track progress
            self.downloaded_ids.add(cite_id)

            # Save progress every 10 downloads
            if len(self.downloaded_ids) % 10 == 0:
                self.save_progress()

            return True

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to download {url}: {e}")
            self.failed_ids.append({
                'cite_id': cite_id,
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            self.failed_ids.append({
                'cite_id': cite_id,
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return False

    def download_constitution(self, url_file: str = 'constitution_urls.json',
                             output_dir: str = 'html_files/constitution',
                             progress_file: str = 'constitution_download_progress.json'):
        """Download all Constitution HTML files"""
        print("\n" + "="*60)
        print("DOWNLOADING OKLAHOMA CONSTITUTION HTML FILES")
        print("="*60)

        # Load URLs and progress
        urls = self.load_urls(url_file)
        if not urls:
            print("[ERROR] No URLs to download")
            return

        self.load_progress(progress_file)

        # Calculate what needs to be downloaded
        to_download = [u for u in urls if u['cite_id'] not in self.downloaded_ids]

        print(f"\nDownload Plan:")
        print(f"  Total sections: {len(urls)}")
        print(f"  Already downloaded: {len(self.downloaded_ids)}")
        print(f"  Remaining: {len(to_download)}")
        print(f"  Estimated time: {(len(to_download) * self.delay) / 60:.1f} minutes")
        print()

        # Download each HTML file
        success_count = 0
        for i, url_data in enumerate(to_download, 1):
            cite_id = url_data['cite_id']
            url = url_data['url']

            # Create output path: html_files/constitution/CiteID_<cite_id>.html
            output_path = os.path.join(output_dir, f"CiteID_{cite_id}.html")

            print(f"\nProgress: {i}/{len(to_download)} (Total: {len(self.downloaded_ids)}/{len(urls)})")

            if self.download_html(url, cite_id, output_path):
                success_count += 1

        # Final progress save
        self.save_progress()

        # Summary
        print("\n" + "="*60)
        print("CONSTITUTION DOWNLOAD COMPLETE")
        print("="*60)
        print(f"Successfully downloaded: {success_count} new files")
        print(f"Total downloaded: {len(self.downloaded_ids)}")
        print(f"Failed: {len(self.failed_ids)}")

        if self.failed_ids:
            print(f"\nFailed downloads saved to: {progress_file}")

    def download_statutes(self, url_file: str = 'oklahoma_statute_urls.json',
                         output_dir: str = 'html_files/statutes',
                         progress_file: str = 'statute_download_progress.json'):
        """Download all Statute HTML files"""
        print("\n" + "="*60)
        print("DOWNLOADING OKLAHOMA STATUTES HTML FILES")
        print("="*60)

        # Load URLs and progress
        urls = self.load_urls(url_file)
        if not urls:
            print("[ERROR] No URLs to download")
            return

        self.load_progress(progress_file)

        # Calculate what needs to be downloaded
        to_download = [u for u in urls if u['cite_id'] not in self.downloaded_ids]

        print(f"\nDownload Plan:")
        print(f"  Total sections: {len(urls)}")
        print(f"  Already downloaded: {len(self.downloaded_ids)}")
        print(f"  Remaining: {len(to_download)}")
        print(f"  Estimated time: {(len(to_download) * self.delay) / 60:.1f} minutes")
        print(f"                  ({(len(to_download) * self.delay) / 3600:.1f} hours)")
        print()

        # Download each HTML file, organized by title
        success_count = 0
        for i, url_data in enumerate(to_download, 1):
            cite_id = url_data['cite_id']
            url = url_data['url']
            title_num = url_data.get('title_number', 'unknown')

            # Create output path: html_files/statutes/title_<num>/CiteID_<cite_id>.html
            title_dir = os.path.join(output_dir, f"title_{title_num}")
            output_path = os.path.join(title_dir, f"CiteID_{cite_id}.html")

            print(f"\nProgress: {i}/{len(to_download)} (Total: {len(self.downloaded_ids)}/{len(urls)})")
            print(f"  Title: {title_num}")

            if self.download_html(url, cite_id, output_path):
                success_count += 1

        # Final progress save
        self.save_progress()

        # Summary
        print("\n" + "="*60)
        print("STATUTES DOWNLOAD COMPLETE")
        print("="*60)
        print(f"Successfully downloaded: {success_count} new files")
        print(f"Total downloaded: {len(self.downloaded_ids)}")
        print(f"Failed: {len(self.failed_ids)}")

        if self.failed_ids:
            print(f"\nFailed downloads saved to: {progress_file}")


def main():
    """Main entry point"""
    print("Oklahoma Legal Documents HTML Downloader")
    print("This tool respectfully downloads HTML files from OSCN")
    print()

    # Ask user for preferences
    print("Options:")
    print("1. Download Constitution HTML files (~491 files, ~82 minutes)")
    print("2. Download Statute HTML files (~10,000 files, ~28 hours)")
    print("3. Download both (Constitution first, then Statutes)")
    print()

    choice = input("Enter choice (1-3): ").strip()

    downloader = HTMLDownloader(delay_seconds=10)

    if choice == '1':
        # Download Constitution
        downloader.download_constitution()

    elif choice == '2':
        # Download Statutes
        downloader.download_statutes()

    elif choice == '3':
        # Download both
        print("\n[PHASE 1] Downloading Constitution HTML files...")
        downloader.download_constitution()

        print("\n[PHASE 2] Downloading Statute HTML files...")
        # Reset downloader for statutes
        downloader = HTMLDownloader(delay_seconds=10)
        downloader.download_statutes()

    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        print("Progress has been saved. Run again to resume.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
