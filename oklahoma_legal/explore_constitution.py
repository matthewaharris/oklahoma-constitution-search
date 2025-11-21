#!/usr/bin/env python3
"""
Explore Oklahoma Constitution structure on OSCN to find cite IDs
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urljoin

class ConstitutionExplorer:
    def __init__(self):
        self.base_url = "https://www.oscn.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def explore_constitution_index(self):
        """Find the Oklahoma Constitution index page and extract structure"""
        # Common patterns for constitution URLs on OSCN
        possible_urls = [
            "https://www.oscn.net/applications/OCISWeb/index.asp?level=1&ftdb=STOKCONST",
            "https://www.oscn.net/applications/OCISWeb/index.asp?level=1&ftdb=STOKCONST2020",
            "https://www.oscn.net/applications/OCISWeb/index.asp?level=1&ftdb=STOKCONST2021",
            "https://www.oscn.net/applications/OCISWeb/index.asp?level=1&ftdb=CONST",
            "https://www.oscn.net/applications/OCISWeb/index.asp?level=1&ftdb=OKCONST",
        ]

        constitution_data = []

        print("Exploring possible Constitution URLs...")

        for url in possible_urls:
            print(f"\nTrying: {url}")

            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    print(f"✓ Success! Found constitution at: {url}")

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Save the page for analysis
                    filename = f"constitution_index_{url.split('=')[-1]}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"  Saved page to: {filename}")

                    # Extract links that look like constitution sections
                    links = self.extract_constitution_links(soup, url)
                    if links:
                        constitution_data.extend(links)
                        print(f"  Found {len(links)} potential constitution sections")

                else:
                    print(f"  Status: {response.status_code}")

            except Exception as e:
                print(f"  Error: {e}")

            time.sleep(1)  # Be respectful

        # Try searching for constitution directly
        search_results = self.search_for_constitution()
        if search_results:
            constitution_data.extend(search_results)

        return constitution_data

    def extract_constitution_links(self, soup, base_url):
        """Extract links that look like constitution sections"""
        links = []

        # Look for links containing cite IDs
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()

            # Look for DeliverDocument links (these contain cite IDs)
            if 'DeliverDocument.asp?CiteID=' in href:
                cite_id_match = re.search(r'CiteID=(\d+)', href)
                if cite_id_match:
                    cite_id = cite_id_match.group(1)

                    # Check if this looks like a constitution section
                    if self.looks_like_constitution(text, href):
                        full_url = urljoin(base_url, href)
                        links.append({
                            'cite_id': cite_id,
                            'text': text,
                            'href': href,
                            'full_url': full_url,
                            'source': base_url
                        })

        return links

    def looks_like_constitution(self, text, href):
        """Determine if a link looks like it's for the constitution"""
        constitution_indicators = [
            'article',
            'section',
            'const',
            'constitution',
            'preamble',
            'amendment'
        ]

        text_lower = text.lower()
        href_lower = href.lower()

        return any(indicator in text_lower or indicator in href_lower
                  for indicator in constitution_indicators)

    def search_for_constitution(self):
        """Try to find constitution by searching common patterns"""
        print("\nSearching for constitution using known patterns...")

        # Try some known constitution cite IDs (these are guesses based on common patterns)
        test_cite_ids = [
            # Common ranges where constitutions might be stored
            range(1, 100),      # Very low numbers
            range(400000, 400100), # Similar to our statute range
            range(500000, 500100),
            range(100000, 100100),
        ]

        found_constitution = []

        for cite_range in test_cite_ids:
            print(f"Testing cite ID range {cite_range.start}-{cite_range.stop-1}...")

            # Test a few from each range
            test_ids = list(cite_range)[::10][:5]  # Every 10th ID, max 5 per range

            for cite_id in test_ids:
                url = f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}"

                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        # Check if this looks like constitution content
                        if self.is_constitution_content(response.text):
                            print(f"  ✓ Found constitution content at CiteID: {cite_id}")

                            soup = BeautifulSoup(response.text, 'html.parser')
                            title = soup.find('title')
                            title_text = title.get_text() if title else f"Constitution Section {cite_id}"

                            found_constitution.append({
                                'cite_id': str(cite_id),
                                'text': title_text,
                                'full_url': url,
                                'source': 'direct_search'
                            })

                except Exception as e:
                    pass  # Continue searching

                time.sleep(0.5)  # Small delay

            if found_constitution:
                break  # Found some, stop searching other ranges

        return found_constitution

    def is_constitution_content(self, html):
        """Check if HTML content looks like it's from the constitution"""
        constitution_keywords = [
            'oklahoma constitution',
            'article',
            'preamble',
            'we, the people of oklahoma',
            'state of oklahoma',
            'constitutional',
            'amendment'
        ]

        html_lower = html.lower()
        return any(keyword in html_lower for keyword in constitution_keywords)

    def save_results(self, constitution_data):
        """Save found constitution sections to file"""
        if not constitution_data:
            print("\nNo constitution sections found!")
            return

        print(f"\nFound {len(constitution_data)} potential constitution sections:")
        print("-" * 60)

        for item in constitution_data:
            print(f"CiteID: {item['cite_id']} - {item['text'][:60]}...")

        # Save to JSON file
        with open('oklahoma_constitution_sections.json', 'w', encoding='utf-8') as f:
            json.dump(constitution_data, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to: oklahoma_constitution_sections.json")

        # Create a simple list of cite IDs for bulk scraping
        cite_ids = [item['cite_id'] for item in constitution_data]
        with open('constitution_cite_ids.txt', 'w') as f:
            f.write('\n'.join(cite_ids))

        print(f"Cite IDs saved to: constitution_cite_ids.txt")

        return cite_ids

def main():
    explorer = ConstitutionExplorer()

    print("Oklahoma Constitution Structure Explorer")
    print("=" * 50)

    constitution_data = explorer.explore_constitution_index()
    cite_ids = explorer.save_results(constitution_data)

    if cite_ids:
        print(f"\nNext steps:")
        print(f"1. Review the found sections in oklahoma_constitution_sections.json")
        print(f"2. Run bulk scraper with: python bulk_scrape_constitution.py")
        print(f"3. The scraper will process {len(cite_ids)} sections automatically")
    else:
        print("\nNo constitution sections found. You may need to manually find cite IDs.")
        print("Try browsing to https://www.oscn.net and searching for 'Oklahoma Constitution'")

if __name__ == "__main__":
    main()