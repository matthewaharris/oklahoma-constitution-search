#!/usr/bin/env python3
"""
Oklahoma Case Law Discovery Crawler
Discovers all CiteIDs for cases from 2020-2025 (MVP scope)
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Set
import time
import json
import re
from datetime import datetime

class CaseLawDiscoverer:
    """Discover all case CiteIDs from OSCN"""

    def __init__(self):
        self.base_url = "https://www.oscn.net/applications/oscn/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Oklahoma Legal Research Bot - Educational Purpose)'
        })

        # Court databases to scrape
        self.courts = {
            'supreme_court': 'STOKCSSC',
            'criminal_appeals': 'STOKCSCR',
            'civil_appeals': 'STOKCSCV',
            # 'court_on_judiciary': 'STOKCSJU'  # Uncomment if needed
        }

        # Years to scrape (MVP: 2020-2025)
        self.years = list(range(2020, 2026))  # 2020-2025

        self.discovered_cite_ids = set()
        self.rate_limit_delay = 2  # seconds between requests

    def discover_all_cases(self) -> Dict[str, List[str]]:
        """
        Discover all case CiteIDs from all courts for 2020-2025

        Returns:
            Dict mapping court_type -> list of cite_ids
        """
        all_cases = {}

        for court_name, court_db in self.courts.items():
            print(f"\n{'='*60}")
            print(f"Discovering cases from: {court_name}")
            print(f"Database: {court_db}")
            print(f"{'='*60}\n")

            cite_ids = self.discover_court_cases(court_db, court_name)
            all_cases[court_name] = cite_ids

            print(f"\n[OK] Found {len(cite_ids)} cases in {court_name}")

        return all_cases

    def discover_court_cases(self, court_db: str, court_name: str) -> List[str]:
        """
        Discover all cases for a specific court

        Args:
            court_db: Database code (e.g., "STOKCSSC")
            court_name: Human-readable name

        Returns:
            List of CiteIDs
        """
        cite_ids = []

        for year in self.years:
            print(f"  Discovering {year} cases...")

            year_cite_ids = self.discover_year_cases(court_db, year)
            cite_ids.extend(year_cite_ids)

            print(f"    Found {len(year_cite_ids)} cases for {year}")

            # Rate limiting
            time.sleep(self.rate_limit_delay)

        return cite_ids

    def discover_year_cases(self, court_db: str, year: int) -> List[str]:
        """
        Discover all cases for a specific year using multiple strategies

        Args:
            court_db: Database code
            year: Year to scrape

        Returns:
            List of CiteIDs for that year
        """
        all_cite_ids = set()

        # Strategy 1: Use index pages with different levels
        for level in [1, 2, 3, 4, 5]:
            url = f"{self.base_url}Index.asp?ftdb={court_db}&year={year}&level={level}"
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                cite_ids = self.extract_cite_ids(soup)
                all_cite_ids.update(cite_ids)
                time.sleep(0.5)  # Brief delay between level requests
            except requests.exceptions.RequestException as e:
                print(f"      Warning: Level {level} failed: {e}")
                continue

        # Strategy 2: Try search interface for the year
        # OSCN search can find cases by year range
        search_cite_ids = self.search_by_year_range(court_db, year, year)
        all_cite_ids.update(search_cite_ids)

        return list(all_cite_ids)

    def search_by_year_range(self, court_db: str, start_year: int, end_year: int) -> List[str]:
        """
        Use OSCN search interface to find cases by year range

        Args:
            court_db: Database code
            start_year: Start year
            end_year: End year

        Returns:
            List of CiteIDs found via search
        """
        cite_ids = set()

        # OSCN search URL pattern
        # Search for all cases in year range (wildcard search)
        search_url = f"{self.base_url}Search.asp"

        # Search parameters - try to match all cases in year
        params = {
            'ftdb': court_db,
            'year': f"{start_year}-{end_year}",
            'submit': 'Search'
        }

        try:
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract CiteIDs from search results
            page_cite_ids = self.extract_cite_ids(soup)
            cite_ids.update(page_cite_ids)

            # Check for pagination in search results
            # OSCN may paginate large result sets
            cite_ids.update(self.handle_search_pagination(soup, search_url, params))

        except requests.exceptions.RequestException as e:
            print(f"      Search failed for {start_year}-{end_year}: {e}")

        return list(cite_ids)

    def handle_search_pagination(self, soup: BeautifulSoup, base_url: str, base_params: dict) -> Set[str]:
        """
        Handle paginated search results

        Args:
            soup: Current page soup
            base_url: Base URL for requests
            base_params: Base parameters for search

        Returns:
            Set of CiteIDs from all pages
        """
        cite_ids = set()

        # Look for "Next" or page number links
        # OSCN uses various pagination patterns
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip().lower()

            # Check if this is a pagination link
            if 'next' in text or 'page' in text or re.match(r'^\d+$', text):
                if 'Index.asp' in href or 'Search.asp' in href:
                    try:
                        # Extract pagination parameters
                        full_url = f"{self.base_url.rstrip('/')}/{href.lstrip('/')}" if not href.startswith('http') else href
                        response = self.session.get(full_url, timeout=30)
                        response.raise_for_status()
                        page_soup = BeautifulSoup(response.text, 'html.parser')
                        page_cite_ids = self.extract_cite_ids(page_soup)
                        cite_ids.update(page_cite_ids)
                        time.sleep(1)  # Rate limiting
                    except:
                        continue

        return cite_ids

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

    def save_discovered_cases(self, all_cases: Dict[str, List[str]], filename: str = "discovered_cases.json"):
        """
        Save discovered CiteIDs to JSON file

        Args:
            all_cases: Dictionary of court -> cite_ids
            filename: Output filename
        """
        output = {
            'discovery_date': datetime.now().isoformat(),
            'years_covered': self.years,
            'courts': self.courts,
            'total_cases': sum(len(cite_ids) for cite_ids in all_cases.values()),
            'cases_by_court': all_cases
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n[OK] Saved discovered cases to: {filename}")
        print(f"  Total cases found: {output['total_cases']}")

    def load_discovered_cases(self, filename: str = "discovered_cases.json") -> Dict[str, List[str]]:
        """
        Load previously discovered CiteIDs from JSON file

        Args:
            filename: Input filename

        Returns:
            Dictionary of court -> cite_ids
        """
        with open(filename, 'r') as f:
            data = json.load(f)

        return data['cases_by_court']


def main():
    """Run case law discovery"""
    print("="*60)
    print("Oklahoma Case Law Discovery Crawler")
    print("MVP Scope: 2020-2025")
    print("="*60)

    discoverer = CaseLawDiscoverer()

    # Discover all cases
    all_cases = discoverer.discover_all_cases()

    # Save results
    discoverer.save_discovered_cases(all_cases)

    # Print summary
    print("\n" + "="*60)
    print("DISCOVERY SUMMARY")
    print("="*60)

    for court_name, cite_ids in all_cases.items():
        print(f"{court_name:25} {len(cite_ids):,} cases")

    total = sum(len(cite_ids) for cite_ids in all_cases.values())
    print(f"{'TOTAL':25} {total:,} cases")
    print("="*60)


if __name__ == "__main__":
    main()
