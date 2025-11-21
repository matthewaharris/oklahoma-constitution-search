#!/usr/bin/env python3
"""
Oklahoma Attorney General Opinion Discovery Crawler
Discovers all CiteIDs for AG opinions from 2020-2025 (MVP scope)
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Set
import time
import json
import re
from datetime import datetime

class AGOpinionDiscoverer:
    """Discover all AG opinion CiteIDs from OSCN"""

    def __init__(self):
        self.base_url = "https://www.oscn.net/applications/oscn/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Oklahoma Legal Research Bot - Educational Purpose)'
        })

        # AG opinions database
        self.ag_database = 'STOKAG'

        # Years to scrape (MVP: 2020-2025)
        self.years = list(range(2020, 2026))  # 2020-2025

        self.discovered_cite_ids = set()
        self.rate_limit_delay = 2  # seconds between requests

    def discover_all_opinions(self) -> List[str]:
        """
        Discover all AG opinion CiteIDs for 2020-2025

        Returns:
            List of cite_ids
        """
        print("="*60)
        print("Oklahoma Attorney General Opinion Discovery Crawler")
        print("MVP Scope: 2020-2025")
        print("="*60)

        cite_ids = []

        for year in self.years:
            print(f"\n  Discovering {year} AG opinions...")

            year_cite_ids = self.discover_year_opinions(year)
            cite_ids.extend(year_cite_ids)

            print(f"    Found {len(year_cite_ids)} opinions for {year}")

            # Rate limiting
            time.sleep(self.rate_limit_delay)

        return cite_ids

    def discover_year_opinions(self, year: int) -> List[str]:
        """
        Discover all AG opinions for a specific year

        Args:
            year: Year to scrape

        Returns:
            List of CiteIDs for that year
        """
        # URL pattern for year-level index
        url = f"{self.base_url}Index.asp?ftdb={self.ag_database}&year={year}&level=1"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all links to DeliverDocument.asp with CiteID
            cite_ids = self.extract_cite_ids(soup)

            return cite_ids

        except requests.exceptions.RequestException as e:
            print(f"    ERROR fetching {url}: {e}")
            return []

    def extract_cite_ids(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract CiteIDs from page HTML

        Args:
            soup: BeautifulSoup object

        Returns:
            List of unique CiteIDs
        """
        cite_ids = set()

        # Find all links to DeliverDocument.asp
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Match pattern: DeliverDocument.asp?CiteID=XXXXX
            match = re.search(r'DeliverDocument\.asp\?CiteID=(\d+)', href, re.IGNORECASE)
            if match:
                cite_id = match.group(1)
                cite_ids.add(cite_id)

        return list(cite_ids)

    def save_discovered_opinions(self, cite_ids: List[str], filename: str = "discovered_ag_opinions.json"):
        """
        Save discovered CiteIDs to JSON file

        Args:
            cite_ids: List of cite_ids
            filename: Output filename
        """
        output = {
            'discovery_date': datetime.now().isoformat(),
            'years_covered': self.years,
            'database': self.ag_database,
            'total_opinions': len(cite_ids),
            'cite_ids': cite_ids
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n[OK] Saved discovered AG opinions to: {filename}")
        print(f"  Total opinions found: {len(cite_ids)}")

    def load_discovered_opinions(self, filename: str = "discovered_ag_opinions.json") -> List[str]:
        """
        Load previously discovered CiteIDs from JSON file

        Args:
            filename: Input filename

        Returns:
            List of cite_ids
        """
        with open(filename, 'r') as f:
            data = json.load(f)

        return data['cite_ids']


def main():
    """Run AG opinion discovery"""
    print("="*60)
    print("Oklahoma Attorney General Opinion Discovery Crawler")
    print("MVP Scope: 2020-2025")
    print("="*60)

    discoverer = AGOpinionDiscoverer()

    # Discover all opinions
    cite_ids = discoverer.discover_all_opinions()

    # Save results
    discoverer.save_discovered_opinions(cite_ids)

    # Print summary
    print("\n" + "="*60)
    print("DISCOVERY SUMMARY")
    print("="*60)
    print(f"Total AG Opinions: {len(cite_ids):,}")
    print("="*60)


if __name__ == "__main__":
    main()
