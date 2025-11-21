#!/usr/bin/env python3
"""
Final Oklahoma Statutes Scraper for OSCN (Oklahoma State Courts Network)
Optimized version with improved text processing and structure detection
"""

import requests
from bs4 import BeautifulSoup, NavigableString, Comment
import time
import json
import re
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalOklahomaStatutesScraper:
    def __init__(self):
        self.base_url = "https://www.oscn.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_page(self, url):
        """Fetch a page with error handling"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def clean_text(self, text):
        """Clean extracted text by removing extra whitespace and line breaks"""
        if not text:
            return ""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove carriage returns
        text = text.replace('\r', '')
        return text.strip()

    def extract_statute_metadata(self, soup):
        """Extract statute metadata from the HTML"""
        metadata = {}

        # Extract title from the document header
        title_div = soup.find('div', class_='document_header')
        if title_div:
            # The title structure is in the STRONG tag within the P tag
            strong_tag = title_div.find('strong')
            if strong_tag:
                title_text = strong_tag.get_text()

                # Extract title number (e.g., "Title 68")
                title_match = re.search(r'Title (\d+[A-Z]?)\.\s*(.+?)(?:\n|Chapter)', title_text, re.DOTALL)
                if title_match:
                    metadata['title_number'] = title_match.group(1)
                    metadata['title_name'] = self.clean_text(title_match.group(2))

                # Extract chapter
                chapter_match = re.search(r'Chapter (\d+[A-Z]?)\s*-\s*(.+?)(?:\n|Article)', title_text, re.DOTALL)
                if chapter_match:
                    metadata['chapter_number'] = chapter_match.group(1)
                    metadata['chapter_name'] = self.clean_text(chapter_match.group(2))

                # Extract article if present
                article_match = re.search(r'Article (?:Article )?(\d+[A-Z]?)\s*-\s*(.+?)(?:\n|Section)', title_text, re.DOTALL)
                if article_match:
                    metadata['article_number'] = article_match.group(1)
                    metadata['article_name'] = self.clean_text(article_match.group(2))

                # Extract section
                section_match = re.search(r'Section\s+(\d+[A-Z]?)\s*-\s*(.+?)(?:\n|$)', title_text, re.DOTALL)
                if section_match:
                    metadata['section_number'] = section_match.group(1)
                    metadata['section_name'] = self.clean_text(section_match.group(2))

        # Extract page title
        title_element = soup.find('title')
        if title_element:
            metadata['page_title'] = self.clean_text(title_element.get_text())

        # Extract from the statutes title bar
        title_bar = soup.find('div', id='statutes-title')
        if title_bar:
            metadata['title_bar'] = self.clean_text(title_bar.get_text())

        # Extract citation format
        cite_element = title_div.find('font', size='1') if title_div else None
        if cite_element and 'Cite as:' in cite_element.get_text():
            metadata['citation_format'] = self.clean_text(cite_element.get_text())

        return metadata

    def extract_statute_content(self, soup):
        """Extract the actual statute text content with better parsing"""
        content = {}

        # Method 1: Use document markers
        html_text = str(soup)
        begin_marker = "<!--BEGIN DOCUMENT-->"
        end_marker = "<!--END DOCUMENT-->"

        begin_idx = html_text.find(begin_marker)
        end_idx = html_text.find(end_marker)

        if begin_idx != -1 and end_idx != -1:
            content_html = html_text[begin_idx + len(begin_marker):end_idx]
            content_soup = BeautifulSoup(content_html, 'html.parser')

            # Remove any script tags that might be in the content
            for script in content_soup.find_all('script'):
                script.decompose()

            # Extract main content paragraphs (before Historical Data)
            paragraphs = content_soup.find_all('p')
            content['paragraphs'] = []
            content['definitions'] = []  # For definition-style statutes

            historical_started = False
            for para in paragraphs:
                para_text = self.clean_text(para.get_text())

                if not para_text or para_text in ['', ' ']:
                    continue

                # Check if we've reached historical data
                if re.search(r'Historical\s+Data|Laws\s+\d{4}', para_text, re.IGNORECASE):
                    historical_started = True

                if not historical_started:
                    # Check if this is a numbered definition
                    definition_match = re.match(r'^(\d+)\.\s*"([^"]+)"\s*means\s*(.+)', para_text)
                    if definition_match:
                        content['definitions'].append({
                            'number': definition_match.group(1),
                            'term': definition_match.group(2),
                            'definition': definition_match.group(3)
                        })

                    content['paragraphs'].append({
                        'text': para_text,
                        'is_historical': historical_started
                    })

            # Extract main text without historical data
            main_paragraphs = [p for p in content['paragraphs'] if not p.get('is_historical', False)]
            content['main_text'] = '\n\n'.join([p['text'] for p in main_paragraphs])

        # Extract historical/legislative data separately
        content['historical_data'] = self.extract_historical_data(soup)

        # Extract any superseded document links
        superseded_links = soup.find_all('a', string=re.compile(r'superseded document available'))
        if superseded_links:
            content['superseded_documents'] = []
            for link in superseded_links:
                content['superseded_documents'].append({
                    'text': link.get_text(),
                    'href': link.get('href')
                })

        return content

    def extract_historical_data(self, soup):
        """Extract historical and legislative information"""
        historical_data = {}

        # Find the historical data section
        html_text = str(soup)

        # Look for Laws section with year patterns
        laws_pattern = r'Laws\s+(\d{4}),\s+([HS]B\s+\d+)[^.]*?\.([^.]*?)(?=Laws|\.|$)'
        laws_matches = re.finditer(laws_pattern, html_text, re.DOTALL | re.IGNORECASE)

        laws_entries = []
        for match in laws_matches:
            laws_entries.append({
                'year': match.group(1),
                'bill': match.group(2),
                'details': self.clean_text(match.group(3))
            })

        if laws_entries:
            historical_data['legislative_history'] = laws_entries

        # Look for effective dates
        eff_date_pattern = r'eff?\.\s*([^;,.\n]+)'
        eff_dates = re.findall(eff_date_pattern, html_text, re.IGNORECASE)
        if eff_dates:
            historical_data['effective_dates'] = [self.clean_text(date) for date in eff_dates]

        return historical_data

    def extract_citations_and_references(self, soup):
        """Extract citation information and cross-references"""
        citations = {}

        # Find the Citationizer table
        tables = soup.find_all('table')
        for table in tables:
            headers = table.find_all('th')
            if headers and any('Cite' in th.get_text() for th in headers):
                rows = table.find_all('tr')[1:]  # Skip header
                citation_list = []

                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # Skip the "None Found" rows
                        if 'None Found' in cells[0].get_text():
                            continue

                        cite_cell = cells[0] if len(cells) > 1 else None
                        name_cell = cells[1] if len(cells) > 1 else None
                        level_cell = cells[2] if len(cells) > 2 else None

                        # Look for links in the cells
                        cite_link = cite_cell.find('a') if cite_cell else None
                        name_link = name_cell.find('a') if name_cell else None

                        if cite_link or name_link:
                            citation_entry = {}
                            if cite_link:
                                citation_entry['cite'] = self.clean_text(cite_link.get_text())
                                citation_entry['cite_href'] = cite_link.get('href')
                            if name_link:
                                citation_entry['name'] = self.clean_text(name_link.get_text())
                                citation_entry['name_href'] = name_link.get('href')
                            if level_cell:
                                citation_entry['level'] = self.clean_text(level_cell.get_text())

                            citation_list.append(citation_entry)

                if citation_list:
                    citations['references'] = citation_list

        return citations

    def scrape_statute(self, cite_id):
        """Scrape a single statute by its cite ID"""
        url = f"{self.base_url}/applications/oscn/DeliverDocument.asp?CiteID={cite_id}"
        logger.info(f"Scraping statute: {url}")

        html = self.get_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract all components
        result = {
            'cite_id': cite_id,
            'url': url,
            'metadata': self.extract_statute_metadata(soup),
            'content': self.extract_statute_content(soup),
            'citations': self.extract_citations_and_references(soup),
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'scraper_version': '1.0'
        }

        return result

    def search_statutes(self, title_number=None, chapter_number=None, section_number=None):
        """Search for statutes by title, chapter, and/or section"""
        if title_number:
            # This would require exploration of the index structure
            # For now, return a placeholder
            logger.info(f"Searching for Title {title_number} statutes")
            # Implementation would go here
            pass

    def bulk_scrape_title(self, title_number, max_statutes=None, delay=1):
        """Bulk scrape all statutes in a title"""
        logger.info(f"Starting bulk scrape of Title {title_number}")

        # This would require implementing index traversal
        # For now, return placeholder
        results = []
        return results

def test_final_scraper():
    """Test the final scraper with improved parsing"""
    scraper = FinalOklahomaStatutesScraper()

    # Test with multiple statute IDs
    test_statutes = [
        '440462',  # Our test statute - definitions
        # Add more if you have other cite IDs to test
    ]

    for cite_id in test_statutes:
        print(f"\n{'='*60}")
        print(f"TESTING STATUTE {cite_id}")
        print('='*60)

        result = scraper.scrape_statute(cite_id)

        if result:
            print(f"[SUCCESS] Successfully scraped statute {cite_id}")

            # Display metadata
            print("\n[METADATA]:")
            metadata = result['metadata']
            for key, value in metadata.items():
                print(f"  {key}: {value}")

            # Display content summary
            print("\n[CONTENT SUMMARY]:")
            content = result['content']

            if 'definitions' in content and content['definitions']:
                print(f"  [DEFINITIONS] Found {len(content['definitions'])} definitions:")
                for defn in content['definitions'][:3]:  # Show first 3
                    print(f"    {defn['number']}. {defn['term']}: {defn['definition'][:100]}...")

            if 'main_text' in content:
                print(f"  [TEXT] Main text length: {len(content['main_text'])} characters")
                print(f"  [PREVIEW] {content['main_text'][:150]}...")

            if 'historical_data' in content and content['historical_data']:
                print(f"  [HISTORICAL] {content['historical_data']}")

            # Display citations
            if 'citations' in result and result['citations']:
                print(f"\n[CITATIONS] {len(result['citations'].get('references', []))} found")

            # Save individual result
            filename = f'statute_{cite_id}_final.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"  [SAVED] to: {filename}")

        else:
            print(f"[FAILED] Failed to scrape statute {cite_id}")

if __name__ == "__main__":
    test_final_scraper()