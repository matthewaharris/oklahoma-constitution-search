#!/usr/bin/env python3
"""
Oklahoma Statutes URL Collector
Respectfully discovers statute URLs from OSCN with long delays
"""

import requests
import time
import json
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from datetime import datetime
from urllib.parse import urljoin

class StatuteURLCollector:
    def __init__(self, delay_seconds: int = 10):
        """
        Initialize URL collector

        Args:
            delay_seconds: Seconds to wait between requests (default 10)
        """
        self.delay = delay_seconds
        self.base_url = "https://www.oscn.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Legal Research Tool - Contact: mharris26@gmail.com)'
        })
        self.collected_urls = []

    def get_constitution_index_url(self) -> str:
        """Get the index URL for the Oklahoma Constitution"""
        return f"{self.base_url}/applications/oscn/Index.asp?ftdb=STOKCN&level=1"

    def get_title_index_url(self, title_number: int) -> str:
        """Get the index URL for a specific title"""
        return f"{self.base_url}/applications/oscn/Index.asp?ftdb=STOKST{title_number}&level=1"

    def fetch_page_safe(self, url: str) -> str:
        """Fetch a page with error handling and delays"""
        print(f"Fetching: {url}")
        print(f"Waiting {self.delay} seconds...")
        time.sleep(self.delay)

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            print(f"[OK] Status: {response.status_code}")
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch {url}: {e}")
            return None

    def extract_statute_links(self, html: str, title_number: int, page_url: str) -> List[Dict]:
        """Extract all statute links from a title index page"""
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        links = []

        # Find all links that look like statute sections
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')

            # Look for DeliverDocument.asp links (statute sections)
            if 'DeliverDocument.asp' in href and 'CiteID=' in href:
                # Extract cite ID
                cite_match = re.search(r'CiteID=(\d+)', href)
                if cite_match:
                    cite_id = cite_match.group(1)

                    # Build full URL using urljoin (handles relative URLs correctly)
                    full_url = urljoin(page_url, href)

                    # Get link text (section name)
                    link_text = link.get_text(strip=True)

                    links.append({
                        'cite_id': cite_id,
                        'url': full_url,
                        'title_number': title_number,
                        'section_name': link_text,
                        'discovered_at': datetime.now().isoformat()
                    })

        return links

    def extract_constitution_links(self, html: str, page_url: str) -> List[Dict]:
        """Extract all Constitution article links from the index page"""
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        links = []

        # Find all links that look like Constitution sections
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')

            # Look for DeliverDocument.asp links (Constitution sections)
            if 'DeliverDocument.asp' in href and 'CiteID=' in href:
                # Extract cite ID
                cite_match = re.search(r'CiteID=(\d+)', href)
                if cite_match:
                    cite_id = cite_match.group(1)

                    # Build full URL using urljoin
                    full_url = urljoin(page_url, href)

                    # Get link text (article/section name)
                    link_text = link.get_text(strip=True)

                    # Try to extract article number from text
                    article_match = re.search(r'Article\s+(\d+[A-Z]?)', link_text, re.IGNORECASE)
                    article_number = article_match.group(1) if article_match else None

                    links.append({
                        'cite_id': cite_id,
                        'url': full_url,
                        'type': 'constitution',
                        'article_number': article_number,
                        'section_name': link_text,
                        'discovered_at': datetime.now().isoformat()
                    })

        return links

    def collect_constitution(self) -> List[Dict]:
        """Collect all Constitution URLs"""
        print(f"\n{'='*60}")
        print(f"Collecting URLs for Oklahoma Constitution")
        print(f"{'='*60}")

        index_url = self.get_constitution_index_url()
        html = self.fetch_page_safe(index_url)

        if not html:
            print(f"[WARNING] Could not fetch Constitution")
            return []

        links = self.extract_constitution_links(html, index_url)
        print(f"[OK] Found {len(links)} sections in Constitution")

        return links

    def collect_title(self, title_number: int) -> List[Dict]:
        """Collect all statute URLs for a specific title"""
        print(f"\n{'='*60}")
        print(f"Collecting URLs for Title {title_number}")
        print(f"{'='*60}")

        index_url = self.get_title_index_url(title_number)
        html = self.fetch_page_safe(index_url)

        if not html:
            print(f"[WARNING] Could not fetch Title {title_number}")
            return []

        links = self.extract_statute_links(html, title_number, index_url)
        print(f"[OK] Found {len(links)} sections in Title {title_number}")

        return links

    def collect_all_titles(self, start_title: int = 1, end_title: int = 85) -> List[Dict]:
        """Collect URLs for all titles"""
        print("Oklahoma Statutes URL Collection")
        print(f"Collecting Titles {start_title} to {end_title}")
        print(f"Delay between requests: {self.delay} seconds")
        print(f"Estimated time: {(end_title - start_title + 1) * self.delay / 60:.1f} minutes")
        print()

        all_urls = []

        for title in range(start_title, end_title + 1):
            urls = self.collect_title(title)
            all_urls.extend(urls)

            print(f"Progress: {title}/{end_title} titles ({len(all_urls)} URLs so far)")

        print(f"\n{'='*60}")
        print(f"[SUCCESS] Collected {len(all_urls)} statute URLs")
        print(f"{'='*60}")

        return all_urls

    def save_urls(self, urls: List[Dict], filename: str = 'oklahoma_statute_urls.json'):
        """Save collected URLs to JSON file"""
        output = {
            'collected_at': datetime.now().isoformat(),
            'total_urls': len(urls),
            'urls': urls
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n[OK] Saved {len(urls)} URLs to {filename}")

    def collect_and_save(self, start_title: int = 1, end_title: int = 85,
                        output_file: str = 'oklahoma_statute_urls.json'):
        """Main function: collect and save all URLs"""
        urls = self.collect_all_titles(start_title, end_title)
        self.save_urls(urls, output_file)
        return urls


def main():
    """Main entry point"""
    print("Oklahoma Legal Documents URL Collector")
    print("This tool respectfully collects URLs from OSCN")
    print()

    # Ask user for preferences
    print("Options:")
    print("1. Collect Oklahoma Constitution - Takes ~10 seconds")
    print("2. Collect all statute titles (1-85) - Takes ~15 minutes with 10-second delay")
    print("3. Collect specific title range")
    print("4. Test with single title")
    print()

    choice = input("Enter choice (1-4): ").strip()

    collector = StatuteURLCollector(delay_seconds=10)

    if choice == '1':
        # Collect Constitution
        urls = collector.collect_constitution()
        collector.save_urls(urls, 'constitution_urls.json')

    elif choice == '2':
        # Collect all titles
        collector.collect_and_save(1, 85, 'oklahoma_statute_urls.json')

    elif choice == '3':
        # Custom range
        start = int(input("Start title: ").strip())
        end = int(input("End title: ").strip())
        output = f'titles_{start}_to_{end}_urls.json'
        collector.collect_and_save(start, end, output)

    elif choice == '4':
        # Test with single title
        title = int(input("Which title to test (1-85): ").strip())
        urls = collector.collect_title(title)
        collector.save_urls(urls, f'title_{title}_urls.json')

    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCollection interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
