#!/usr/bin/env python3
"""
Oklahoma Constitution scraper with Cloudflare bypass techniques
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
import random
from urllib.parse import urljoin
from integrated_scraper import IntegratedStatutesScraper

class CloudflareBypassScraper:
    def __init__(self):
        self.base_url = "https://www.oscn.net"
        self.constitution_url = "https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKCN&level=1"

        # Create session with more realistic browser headers
        self.session = requests.Session()

        # More comprehensive browser headers to appear human
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })

    def human_delay(self, min_seconds=2, max_seconds=5):
        """Add random human-like delays"""
        delay = random.uniform(min_seconds, max_seconds)
        print(f"  Waiting {delay:.1f} seconds (being respectful)...")
        time.sleep(delay)

    def test_site_access(self):
        """Test if we can access OSCN without being blocked"""
        print("Testing access to OSCN...")

        try:
            # First, try accessing the main page
            response = self.session.get("https://www.oscn.net", timeout=15)
            print(f"Main page status: {response.status_code}")

            if response.status_code == 200:
                if "cloudflare" in response.text.lower() or "checking your browser" in response.text.lower():
                    print("❌ Cloudflare challenge detected on main page")
                    return False
                else:
                    print("✓ Main page accessible")

            # Test the constitution page
            self.human_delay(2, 4)

            response = self.session.get(self.constitution_url, timeout=15)
            print(f"Constitution page status: {response.status_code}")

            if response.status_code == 200:
                if "cloudflare" in response.text.lower() or "checking your browser" in response.text.lower():
                    print("❌ Cloudflare challenge detected on constitution page")
                    return False
                else:
                    print("✓ Constitution page accessible")
                    return True
            else:
                print(f"❌ Constitution page returned status {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing site access: {e}")
            return False

    def get_constitution_with_retry(self, max_retries=3):
        """Get constitution with retry logic and better error handling"""
        print(f"Fetching Oklahoma Constitution from: {self.constitution_url}")

        for attempt in range(max_retries):
            try:
                print(f"\nAttempt {attempt + 1}/{max_retries}")

                # Add human-like delay between attempts
                if attempt > 0:
                    self.human_delay(5, 10)

                response = self.session.get(self.constitution_url, timeout=20)

                print(f"Response status: {response.status_code}")
                print(f"Response size: {len(response.text)} characters")

                if response.status_code == 200:
                    # Check for Cloudflare challenge
                    if ("cloudflare" in response.text.lower() or
                        "checking your browser" in response.text.lower() or
                        "just a moment" in response.text.lower()):
                        print("❌ Cloudflare challenge detected")

                        # Save the challenge page for debugging
                        with open(f'cloudflare_challenge_attempt_{attempt + 1}.html', 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        print(f"  Saved challenge page to: cloudflare_challenge_attempt_{attempt + 1}.html")

                        if attempt == max_retries - 1:
                            return None
                        continue

                    # Success! Save and parse the page
                    with open('constitution_root_page.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print("✓ Successfully saved constitution page")

                    return self.parse_constitution_page(response.text)

                elif response.status_code == 403:
                    print("❌ 403 Forbidden - likely blocked by Cloudflare")
                    if attempt == max_retries - 1:
                        return None

                elif response.status_code == 503:
                    print("❌ 503 Service Unavailable - Cloudflare protection active")
                    if attempt == max_retries - 1:
                        return None

                else:
                    print(f"❌ Unexpected status code: {response.status_code}")

            except requests.exceptions.Timeout:
                print("❌ Request timed out")
            except Exception as e:
                print(f"❌ Error: {e}")

        return None

    def parse_constitution_page(self, html_content):
        """Parse the constitution page HTML"""
        print("Parsing constitution page...")

        soup = BeautifulSoup(html_content, 'html.parser')

        # Look for constitution sections
        links = soup.find_all('a', href=True)
        print(f"Found {len(links)} total links")

        constitution_sections = []

        for link in links:
            href = link['href']
            text = link.get_text().strip()

            if 'DeliverDocument.asp?CiteID=' in href:
                cite_id_match = re.search(r'CiteID=(\d+)', href)
                if cite_id_match:
                    cite_id = cite_id_match.group(1)
                    full_url = urljoin(self.base_url, href)

                    constitution_sections.append({
                        'cite_id': cite_id,
                        'text': text,
                        'href': href,
                        'full_url': full_url
                    })

        print(f"✓ Found {len(constitution_sections)} constitution sections")

        # Show preview
        if constitution_sections:
            print("\nFirst 5 sections:")
            for i, section in enumerate(constitution_sections[:5]):
                print(f"  {i+1}. CiteID {section['cite_id']}: {section['text'][:60]}...")

        return constitution_sections

def main():
    print("Oklahoma Constitution Scraper with Cloudflare Bypass")
    print("=" * 60)

    scraper = CloudflareBypassScraper()

    # Test site access first
    if not scraper.test_site_access():
        print("\n❌ SITE ACCESS BLOCKED")
        print("=" * 40)
        print("Cloudflare is blocking automated access to OSCN.")
        print("\nOptions to try:")
        print("1. Manual browsing: Visit the URLs manually in a browser and save the HTML")
        print("2. Selenium automation: Use browser automation tools")
        print("3. Different IP/VPN: Try from a different network")
        print("4. Contact OSCN: Request API access or permission")
        return

    print("\n✓ SITE ACCESS SUCCESSFUL")
    print("=" * 40)

    # Get constitution structure
    sections = scraper.get_constitution_with_retry()

    if not sections:
        print("\n❌ Failed to get constitution sections")
        print("Check the saved HTML files for debugging")
        return

    # Save the found sections
    with open('oklahoma_constitution_sections.json', 'w', encoding='utf-8') as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)

    cite_ids = [section['cite_id'] for section in sections]
    with open('constitution_cite_ids.txt', 'w') as f:
        f.write('\n'.join(cite_ids))

    print(f"\n✓ Saved {len(sections)} sections to files")

    # Ask about bulk scraping
    response = input(f"\nProceed with scraping {len(cite_ids)} sections? (y/n): ").lower()

    if response == 'y':
        print("\nStarting careful bulk scrape with human-like delays...")

        # Use longer delays for bulk scraping to avoid detection
        integrated_scraper = IntegratedStatutesScraper(delay_seconds=3.0)
        results = integrated_scraper.bulk_scrape_statutes(cite_ids)

        print(f"\nScraping completed!")
        print(f"Success: {results['successful']}, Failed: {results['failed']}")
    else:
        print("Scraping cancelled. Files saved for manual review.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()