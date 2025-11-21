#!/usr/bin/env python3
"""
Oklahoma Attorney General Opinion Scraper & Parser
Scrapes individual AG opinion pages and extracts structured data
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

class AGOpinionParser:
    """Parse AG opinion HTML and extract structured data"""

    def parse_opinion(self, html: str, cite_id: str) -> Optional[Dict]:
        """
        Parse AG opinion HTML and extract all metadata and content

        Args:
            html: Raw HTML from OSCN
            cite_id: CiteID for this opinion

        Returns:
            Dictionary with opinion data, or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Extract citation from meta tags or page content
            citation = self.extract_citation(soup)
            if not citation:
                print(f"  WARNING: Could not extract citation for CiteID {cite_id}")
                citation = f"CiteID {cite_id}"  # Fallback

            # Extract other fields
            opinion_data = {
                'cite_id': cite_id,
                'citation': citation,
                'opinion_number': self.extract_opinion_number(soup, citation),
                'opinion_date': self.extract_opinion_date(soup),
                'opinion_year': self.extract_opinion_year(soup, citation),
                'requestor_name': self.extract_requestor_name(soup),
                'requestor_title': self.extract_requestor_title(soup),
                'requestor_organization': self.extract_requestor_organization(soup),
                'opinion_text': self.extract_opinion_text(soup),
                'question_presented': self.extract_question_presented(soup),
                'conclusion': self.extract_conclusion(soup),
                'statutes_cited': self.extract_statute_citations(soup),
                'cases_cited': self.extract_case_citations(soup),
                'oscn_url': f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}"
            }

            return opinion_data

        except Exception as e:
            print(f"  ERROR parsing CiteID {cite_id}: {e}")
            return None

    def extract_citation(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract official citation (e.g., '2025 OK AG 3')"""
        # Try meta tag first
        meta = soup.find('meta', {'name': 'citation'})
        if meta and meta.get('content'):
            return meta['content'].strip()

        # Try to find in page title or header
        title = soup.find('title')
        if title:
            # Pattern: "2025 OK AG 3"
            match = re.search(r'\d{4}\s+OK\s+AG\s+\d+', title.text)
            if match:
                return match.group(0)

        # Look in page content for citation pattern
        text = soup.get_text()
        match = re.search(r'\d{4}\s+OK\s+AG\s+\d+', text)
        if match:
            return match.group(0)

        return None

    def extract_opinion_number(self, soup: BeautifulSoup, citation: str) -> Optional[int]:
        """Extract opinion number from citation"""
        if citation:
            match = re.search(r'AG\s+(\d+)', citation)
            if match:
                return int(match.group(1))
        return None

    def extract_opinion_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract opinion date in YYYY-MM-DD format"""
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

    def extract_opinion_year(self, soup: BeautifulSoup, citation: str) -> Optional[int]:
        """Extract opinion year from citation or date"""
        if citation:
            match = re.search(r'(\d{4})\s+OK\s+AG', citation)
            if match:
                return int(match.group(1))

        opinion_date = self.extract_opinion_date(soup)
        if opinion_date:
            return int(opinion_date.split('-')[0])

        return None

    def extract_requestor_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract requestor name"""
        text = soup.get_text()

        # Look for "Question Submitted by:" or "Submitted by:"
        patterns = [
            r'Question Submitted by:\s*([A-Z][^\n]+)',
            r'Submitted by:\s*([A-Z][^\n]+)',
            r'Requestor:\s*([A-Z][^\n]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Remove trailing commas or extra info
                name = re.sub(r',.*$', '', name).strip()
                return name[:200]  # Limit length

        return None

    def extract_requestor_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract requestor title"""
        text = soup.get_text()

        # Common titles to look for
        titles = [
            'State Representative',
            'State Senator',
            'Commissioner',
            'Director',
            'Chairman',
            'Secretary',
            'Executive Director',
            'County Attorney',
            'District Attorney'
        ]

        for title in titles:
            if title in text:
                return title

        return None

    def extract_requestor_organization(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract requestor organization"""
        text = soup.get_text()

        # Look for common organization patterns
        patterns = [
            r'Oklahoma\s+[A-Z][a-zA-Z\s]+(?:Commission|Department|Board|Authority)',
            r'[A-Z][a-zA-Z\s]+(?:Commission|Department|Board|Authority)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                org = match.group(0).strip()
                if len(org) < 100:  # Reasonable length
                    return org

        return None

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

    def extract_question_presented(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the question presented"""
        text = soup.get_text()

        # Look for question section
        patterns = [
            r'QUESTION[:\s]+(.+?)(?:\n\n|CONCLUSION|OPINION)',
            r'Question Presented[:\s]+(.+?)(?:\n\n|CONCLUSION|OPINION)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                question = match.group(1).strip()
                # Limit length
                if len(question) < 1000:
                    return question

        return None

    def extract_conclusion(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract conclusion"""
        text = soup.get_text()

        # Look for conclusion section
        patterns = [
            r'CONCLUSION[:\s]+(.+?)(?:\n\n[A-Z]+|$)',
            r'(?:In conclusion|Therefore)[,:\s]+(.+?)(?:\n\n|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                conclusion = match.group(1).strip()
                # Limit length
                if len(conclusion) < 2000:
                    return conclusion

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
            r'\d{4}\s+OK\s+(?:CR\s+)?(?:AG\s+)?\d+',
            r'\d+\s+P\.\d+d\s+\d+'
        ]

        citations = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.update(matches)

        return list(citations)[:100]  # Limit to 100 citations


class AGOpinionScraper:
    """Scrape AG opinions and store in Supabase"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.parser = AGOpinionParser()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Oklahoma Legal Research Bot - Educational Purpose)'
        })

        # Initialize Supabase
        self.supabase = create_client(supabase_url, supabase_key)

        self.rate_limit_delay = 2  # seconds between requests
        self.batch_size = 10  # Insert in batches

    def scrape_opinion(self, cite_id: str) -> Optional[Dict]:
        """
        Scrape a single AG opinion by CiteID

        Args:
            cite_id: OSCN CiteID

        Returns:
            Parsed opinion data or None
        """
        url = f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            opinion_data = self.parser.parse_opinion(response.text, cite_id)

            return opinion_data

        except requests.exceptions.RequestException as e:
            print(f"  ERROR fetching CiteID {cite_id}: {e}")
            return None

    def scrape_opinions_batch(self, cite_ids: List[str]) -> List[Dict]:
        """Scrape multiple opinions with rate limiting"""
        opinions = []

        for i, cite_id in enumerate(cite_ids):
            print(f"  Scraping {i+1}/{len(cite_ids)}: CiteID {cite_id}")

            opinion_data = self.scrape_opinion(cite_id)

            if opinion_data:
                opinions.append(opinion_data)

            # Rate limiting
            time.sleep(self.rate_limit_delay)

        return opinions

    def store_opinions(self, opinions: List[Dict]) -> int:
        """
        Store AG opinions in Supabase

        Returns:
            Number of opinions successfully stored
        """
        if not opinions:
            return 0

        stored_count = 0

        # Insert in batches
        for i in range(0, len(opinions), self.batch_size):
            batch = opinions[i:i + self.batch_size]

            try:
                result = self.supabase.table('attorney_general_opinions').insert(batch).execute()
                stored_count += len(batch)
                print(f"  Stored batch: {stored_count}/{len(opinions)} opinions")

            except Exception as e:
                print(f"  ERROR storing batch: {e}")

        return stored_count


def main():
    """Test the AG opinion scraper with a sample"""
    print("="*60)
    print("Oklahoma Attorney General Opinion Scraper - Test")
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
    scraper = AGOpinionScraper(supabase_url, supabase_key)

    # Test with an example AG opinion (you'll need to provide a valid CiteID)
    test_cite_id = "547774"  # Placeholder - update with actual AG opinion CiteID

    print(f"\nTesting with CiteID: {test_cite_id}")
    opinion_data = scraper.scrape_opinion(test_cite_id)

    if opinion_data:
        print("\n" + "="*60)
        print("SUCCESSFULLY PARSED AG OPINION")
        print("="*60)
        print(f"Citation: {opinion_data['citation']}")
        print(f"Opinion Number: {opinion_data['opinion_number']}")
        print(f"Opinion Date: {opinion_data['opinion_date']}")
        print(f"Requestor: {opinion_data['requestor_name']}")
        print(f"Opinion Length: {len(opinion_data['opinion_text'])} characters")
        print(f"Statutes Cited: {len(opinion_data['statutes_cited'])}")
        print(f"Cases Cited: {len(opinion_data['cases_cited'])}")
    else:
        print("\nERROR: Failed to parse AG opinion")


if __name__ == "__main__":
    main()
