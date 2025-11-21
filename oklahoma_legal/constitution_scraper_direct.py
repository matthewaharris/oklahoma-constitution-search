#!/usr/bin/env python3
"""
Direct Oklahoma Constitution scraper using the known root page
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urljoin
from integrated_scraper import IntegratedStatutesScraper

class DirectConstitutionScraper:
    def __init__(self):
        self.base_url = "https://www.oscn.net"
        self.constitution_url = "https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKCN&level=1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_constitution_structure(self):
        """Get the constitution structure from the known root page"""
        print(f"Fetching Oklahoma Constitution from: {self.constitution_url}")

        try:
            response = self.session.get(self.constitution_url, timeout=15)
            response.raise_for_status()

            print(f"✓ Successfully loaded constitution page (Status: {response.status_code})")

            # Save the page for analysis
            with open('constitution_root_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("✓ Saved page to: constitution_root_page.html")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract all links that contain cite IDs
            constitution_sections = []

            print("\nAnalyzing page structure...")

            # Look for links with DeliverDocument.asp?CiteID=
            links = soup.find_all('a', href=True)
            print(f"Found {len(links)} total links on the page")

            cite_id_links = []
            for link in links:
                href = link['href']
                text = link.get_text().strip()

                if 'DeliverDocument.asp?CiteID=' in href:
                    cite_id_match = re.search(r'CiteID=(\d+)', href)
                    if cite_id_match:
                        cite_id = cite_id_match.group(1)
                        full_url = urljoin(self.base_url, href)

                        cite_id_links.append({
                            'cite_id': cite_id,
                            'text': text,
                            'href': href,
                            'full_url': full_url
                        })

            print(f"✓ Found {len(cite_id_links)} constitution sections with cite IDs")

            # Show first few for verification
            if cite_id_links:
                print("\nFirst 5 sections found:")
                for i, section in enumerate(cite_id_links[:5]):
                    print(f"  {i+1}. CiteID {section['cite_id']}: {section['text'][:60]}...")

            return cite_id_links

        except Exception as e:
            print(f"Error fetching constitution page: {e}")
            return []

    def save_constitution_sections(self, sections):
        """Save the found sections to files"""
        if not sections:
            print("No constitution sections to save!")
            return []

        print(f"\nSaving {len(sections)} constitution sections...")

        # Save complete data
        with open('oklahoma_constitution_sections.json', 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)

        # Save just cite IDs for bulk scraper
        cite_ids = [section['cite_id'] for section in sections]
        with open('constitution_cite_ids.txt', 'w') as f:
            f.write('\n'.join(cite_ids))

        print(f"✓ Saved to: oklahoma_constitution_sections.json")
        print(f"✓ Saved cite IDs to: constitution_cite_ids.txt")

        return cite_ids

    def bulk_scrape_sections(self, cite_ids, force_update=False):
        """Bulk scrape the constitution sections"""
        if not cite_ids:
            print("No cite IDs to scrape!")
            return

        print(f"\nStarting bulk scrape of {len(cite_ids)} Oklahoma Constitution sections...")

        scraper = IntegratedStatutesScraper(delay_seconds=1.5)

        print("Progress will be shown below:")
        print("-" * 60)

        results = scraper.bulk_scrape_statutes(cite_ids, force_update=force_update)

        print("\n" + "=" * 60)
        print("CONSTITUTION SCRAPING COMPLETED!")
        print("=" * 60)

        print(f"Total sections: {results['total_requested']}")
        print(f"Successfully scraped: {results['successful']}")
        print(f"Already existed (skipped): {results['skipped']}")
        print(f"Failed: {results['failed']}")
        print(f"Total time: {results['elapsed_seconds']:.2f} seconds")

        if results['errors']:
            print(f"\nErrors encountered:")
            for error in results['errors'][:3]:
                print(f"  {error['cite_id']}: {error['error'][:100]}...")

        # Save results
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"constitution_scrape_results_{timestamp}.json"

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\nDetailed results saved to: {results_file}")

        return results

def main():
    print("Oklahoma Constitution Direct Scraper")
    print("=" * 50)
    print("Using known root URL: https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKCN&level=1")
    print()

    scraper = DirectConstitutionScraper()

    # Step 1: Get constitution structure
    print("STEP 1: Getting constitution structure...")
    sections = scraper.get_constitution_structure()

    if not sections:
        print("Failed to find constitution sections!")
        return

    # Step 2: Save the found sections
    cite_ids = scraper.save_constitution_sections(sections)

    # Step 3: Ask user if they want to proceed with scraping
    print(f"\nFound {len(cite_ids)} constitution sections to scrape.")
    response = input("Proceed with bulk scraping? (y/n): ").lower()

    if response == 'y':
        print("\nSTEP 2: Starting bulk scrape...")
        results = scraper.bulk_scrape_sections(cite_ids)

        # Step 4: Show final database stats
        if results and (results['successful'] > 0):
            print("\nSTEP 3: Checking database contents...")
            try:
                from supabase_client import StatutesDatabase
                db = StatutesDatabase()
                stats = db.get_database_stats()

                print(f"\nDatabase now contains:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")

            except Exception as e:
                print(f"Error getting database stats: {e}")

        print(f"\n🎉 Constitution scraping completed!")
        print(f"You can now run 'python show_data.py' to see all your data")

    else:
        print("Scraping cancelled. Cite IDs saved for later use.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()