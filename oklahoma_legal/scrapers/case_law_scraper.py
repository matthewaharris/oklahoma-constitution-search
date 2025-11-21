#!/usr/bin/env python3
"""
Oklahoma Case Law Scraper & Parser
Scrapes individual case pages and extracts structured data
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import time
import json
import re
from datetime import datetime
from supabase import create_client
import os

class CaseLawParser:
    """Parse case HTML and extract structured data"""

    def parse_case(self, html: str, cite_id: str, court_type: str, court_database: str) -> Optional[Dict]:
        """
        Parse case HTML and extract all metadata and content

        Args:
            html: Raw HTML from OSCN
            cite_id: CiteID for this case
            court_type: Type of court
            court_database: Database code

        Returns:
            Dictionary with case data, or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Extract citation from meta tags or page content
            citation = self.extract_citation(soup)
            if not citation:
                print(f"  WARNING: Could not extract citation for CiteID {cite_id}")
                citation = f"CiteID {cite_id}"  # Fallback

            # Extract other fields
            case_data = {
                'cite_id': cite_id,
                'citation': citation,
                'case_number': self.extract_case_number(soup),
                'court_type': court_type,
                'court_database': court_database,
                'decision_date': self.extract_decision_date(soup),
                'decision_year': self.extract_decision_year(soup),
                'case_title': self.extract_case_title(soup),
                'appellant': self.extract_party(soup, 'appellant'),
                'appellee': self.extract_party(soup, 'appellee'),
                'other_parties': self.extract_other_parties(soup),
                'authoring_judge': self.extract_authoring_judge(soup),
                'concurring_judges': self.extract_judges(soup, 'concurring'),
                'dissenting_judges': self.extract_judges(soup, 'dissenting'),
                'opinion_text': self.extract_opinion_text(soup),
                'syllabus': self.extract_syllabus(soup),
                'holdings': self.extract_holdings(soup),
                'opinion_type': self.extract_opinion_type(soup),
                'procedural_posture': self.extract_procedural_posture(soup),
                'statutes_cited': self.extract_statute_citations(soup),
                'cases_cited': self.extract_case_citations(soup),
                'oscn_url': f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}"
            }

            return case_data

        except Exception as e:
            print(f"  ERROR parsing CiteID {cite_id}: {e}")
            return None

    def extract_citation(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract official citation (e.g., '2025 OK 2, 562 P.3d 1085')"""
        # Try meta tag first
        meta = soup.find('meta', {'name': 'citation'})
        if meta and meta.get('content'):
            return meta['content'].strip()

        # Try to find in page title or header
        title = soup.find('title')
        if title:
            # Pattern: "2025 OK 2" or similar
            match = re.search(r'\d{4}\s+OK\s+(?:AG\s+)?\d+', title.text)
            if match:
                return match.group(0)

        # Look in page content for citation pattern
        text = soup.get_text()
        match = re.search(r'\d{4}\s+OK\s+\d+,?\s+\d+\s+P\.\d+d\s+\d+', text)
        if match:
            return match.group(0)

        return None

    def extract_case_number(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract docket/case number"""
        # Look for "Case No." or "No." patterns
        text = soup.get_text()
        patterns = [
            r'Case\s+No\.?\s*(\d+)',
            r'No\.?\s+(\d+)',
            r'Docket\s+No\.?\s*(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def extract_decision_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract decision date in YYYY-MM-DD format"""
        text = soup.get_text()

        # Pattern: "January 14, 2025" or "01/14/2025"
        date_patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if pattern == date_patterns[0]:  # Month name format
                        month_name, day, year = match.groups()
                        month_map = {
                            'January': 1, 'February': 2, 'March': 3, 'April': 4,
                            'May': 5, 'June': 6, 'July': 7, 'August': 8,
                            'September': 9, 'October': 10, 'November': 11, 'December': 12
                        }
                        month = month_map.get(month_name)
                        if month:
                            return f"{year}-{month:02d}-{int(day):02d}"
                    else:  # MM/DD/YYYY format
                        month, day, year = match.groups()
                        return f"{year}-{int(month):02d}-{int(day):02d}"
                except:
                    continue

        return None

    def extract_decision_year(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract decision year from citation or date"""
        citation = self.extract_citation(soup)
        if citation:
            match = re.search(r'(\d{4})\s+OK', citation)
            if match:
                return int(match.group(1))

        decision_date = self.extract_decision_date(soup)
        if decision_date:
            return int(decision_date.split('-')[0])

        return None

    def extract_case_title(self, soup: BeautifulSoup) -> str:
        """Extract case title"""
        # Try title tag
        title = soup.find('title')
        if title:
            # Remove citation parts
            title_text = re.sub(r'\d{4}\s+OK\s+\d+.*', '', title.text).strip()
            if title_text:
                return title_text

        # Try to find "v." or "vs." pattern for case names
        text = soup.get_text()
        match = re.search(r'([A-Z][a-zA-Z\s,\.]+)\s+v\.?\s+([A-Z][a-zA-Z\s,\.]+)', text)
        if match:
            return f"{match.group(1).strip()} v. {match.group(2).strip()}"

        return "Unknown Case"

    def extract_party(self, soup: BeautifulSoup, party_type: str) -> Optional[str]:
        """Extract appellant or appellee"""
        text = soup.get_text()

        if party_type == 'appellant':
            patterns = [r'Appellant[:\s]+([A-Z][^\n,]+)', r'Petitioner[:\s]+([A-Z][^\n,]+)']
        else:
            patterns = [r'Appellee[:\s]+([A-Z][^\n,]+)', r'Respondent[:\s]+([A-Z][^\n,]+)']

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()[:200]  # Limit length

        return None

    def extract_other_parties(self, soup: BeautifulSoup) -> List[str]:
        """Extract additional parties"""
        # This is complex - for MVP, return empty list
        return []

    def extract_authoring_judge(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract judge who wrote the opinion"""
        text = soup.get_text()

        # Patterns: "Winchester, J." or "JUSTICE WINCHESTER"
        patterns = [
            r'([A-Z][a-z]+),\s*J\.',
            r'JUSTICE\s+([A-Z][A-Z]+)',
            r'([A-Z][a-z]+),\s*Justice'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def extract_judges(self, soup: BeautifulSoup, judge_type: str) -> List[str]:
        """Extract concurring or dissenting judges"""
        # For MVP, return empty list (complex to parse reliably)
        return []

    def extract_opinion_text(self, soup: BeautifulSoup) -> str:
        """Extract full opinion text"""
        # Remove script and style elements
        for script in soup(['script', 'style', 'meta', 'link']):
            script.decompose()

        # Get text
        text = soup.get_text(separator='\n', strip=True)

        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        return text.strip()

    def extract_syllabus(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract syllabus/headnotes"""
        text = soup.get_text()

        # Look for syllabus section (often marked with paragraph 0)
        match = re.search(r'¶\s*0\s*(.+?)¶\s*1', text, re.DOTALL)
        if match:
            return match.group(1).strip()

        return None

    def extract_holdings(self, soup: BeautifulSoup) -> List[str]:
        """Extract key holdings"""
        # For MVP, return empty list (would need NLP to extract reliably)
        return []

    def extract_opinion_type(self, soup: BeautifulSoup) -> str:
        """Extract opinion type"""
        text = soup.get_text().lower()

        if 'dissenting' in text:
            return 'dissenting'
        elif 'concurring' in text:
            return 'concurring'
        elif 'per curiam' in text:
            return 'per_curiam'

        return 'majority'

    def extract_procedural_posture(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract procedural posture (affirmed, reversed, etc.)"""
        text = soup.get_text().lower()

        postures = ['affirmed', 'reversed', 'remanded', 'reversed and remanded', 'dismissed']

        for posture in postures:
            if posture in text:
                return posture

        return None

    def extract_statute_citations(self, soup: BeautifulSoup) -> List[str]:
        """Extract citations to Oklahoma statutes"""
        text = soup.get_text()

        # Pattern: "43 O.S. § 109" or "Title 43, Section 109"
        patterns = [
            r'\d+\s+O\.S\.(?:\s*§|\s+)\s*\d+(?:\.\d+)?',
            r'Title\s+\d+,\s+Section\s+\d+(?:\.\d+)?'
        ]

        citations = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.update(matches)

        return list(citations)[:50]  # Limit to 50 citations

    def extract_case_citations(self, soup: BeautifulSoup) -> List[str]:
        """Extract citations to other cases"""
        text = soup.get_text()

        # Pattern: "2024 OK 123" or "562 P.3d 1085"
        patterns = [
            r'\d{4}\s+OK\s+(?:CR\s+)?\d+',
            r'\d+\s+P\.\d+d\s+\d+'
        ]

        citations = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.update(matches)

        return list(citations)[:100]  # Limit to 100 citations


class CaseLawScraper:
    """Scrape cases and store in Supabase"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.parser = CaseLawParser()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Oklahoma Legal Research Bot - Educational Purpose)'
        })

        # Initialize Supabase
        self.supabase = create_client(supabase_url, supabase_key)

        self.rate_limit_delay = 2  # seconds between requests
        self.batch_size = 10  # Insert in batches

    def scrape_case(self, cite_id: str, court_type: str, court_database: str) -> Optional[Dict]:
        """
        Scrape a single case by CiteID

        Args:
            cite_id: OSCN CiteID
            court_type: Type of court
            court_database: Database code

        Returns:
            Parsed case data or None
        """
        url = f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            case_data = self.parser.parse_case(
                response.text,
                cite_id,
                court_type,
                court_database
            )

            return case_data

        except requests.exceptions.RequestException as e:
            print(f"  ERROR fetching CiteID {cite_id}: {e}")
            return None

    def scrape_cases_batch(self, cite_ids: List[str], court_type: str, court_database: str) -> List[Dict]:
        """Scrape multiple cases with rate limiting"""
        cases = []

        for i, cite_id in enumerate(cite_ids):
            print(f"  Scraping {i+1}/{len(cite_ids)}: CiteID {cite_id}")

            case_data = self.scrape_case(cite_id, court_type, court_database)

            if case_data:
                cases.append(case_data)

            # Rate limiting
            time.sleep(self.rate_limit_delay)

        return cases

    def store_cases(self, cases: List[Dict]) -> int:
        """
        Store cases in Supabase

        Returns:
            Number of cases successfully stored
        """
        if not cases:
            return 0

        stored_count = 0

        # Insert in batches
        for i in range(0, len(cases), self.batch_size):
            batch = cases[i:i + self.batch_size]

            try:
                result = self.supabase.table('oklahoma_cases').insert(batch).execute()
                stored_count += len(batch)
                print(f"  Stored batch: {stored_count}/{len(cases)} cases")

            except Exception as e:
                print(f"  ERROR storing batch: {e}")

        return stored_count


def main():
    """Test the scraper with a sample case"""
    print("="*60)
    print("Oklahoma Case Law Scraper - Test")
    print("="*60)

    # Load environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("Environment variables not set, trying config.py...")
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config import SUPABASE_URL, SUPABASE_KEY
            supabase_url = SUPABASE_URL
            supabase_key = SUPABASE_KEY
            print("Loaded credentials from config.py")
        except ImportError as e:
            print(f"ERROR: Could not import from config.py: {e}")
            return
        except Exception as e:
            print(f"ERROR: {e}")
            return

    # Initialize scraper
    scraper = CaseLawScraper(supabase_url, supabase_key)

    # Test with the example case from your research
    test_cite_id = "547774"  # 2025 OK 2 (guardianship case)

    print(f"\nTesting with CiteID: {test_cite_id}")
    case_data = scraper.scrape_case(test_cite_id, 'supreme_court', 'STOKCSSC')

    if case_data:
        print("\n" + "="*60)
        print("SUCCESSFULLY PARSED CASE")
        print("="*60)
        print(f"Citation: {case_data['citation']}")
        print(f"Case Title: {case_data['case_title']}")
        print(f"Decision Date: {case_data['decision_date']}")
        print(f"Judge: {case_data['authoring_judge']}")
        print(f"Opinion Length: {len(case_data['opinion_text'])} characters")
        print(f"Statutes Cited: {len(case_data['statutes_cited'])}")
        print(f"Cases Cited: {len(case_data['cases_cited'])}")

        # Ask before storing
        store = input("\nStore this case in Supabase? (y/n): ")
        if store.lower() == 'y':
            stored = scraper.store_cases([case_data])
            print(f"Stored {stored} case(s)")
    else:
        print("\nERROR: Failed to parse case")


if __name__ == "__main__":
    main()
