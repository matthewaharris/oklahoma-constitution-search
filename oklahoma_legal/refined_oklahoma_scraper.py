#!/usr/bin/env python3
"""
Refined Oklahoma Statutes Scraper for OSCN (Oklahoma State Courts Network)
Based on analysis of actual HTML structure
"""

import requests
from bs4 import BeautifulSoup, NavigableString
import time
import json
import re
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RefinedOklahomaStatutesScraper:
    def __init__(self):
        self.base_url = "https://www.oscn.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_page(self, url):
        """Fetch a page with error handling"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_statute_metadata(self, soup):
        """Extract statute metadata from the HTML"""
        metadata = {}

        # Extract title from the document header
        title_div = soup.find('div', class_='document_header')
        if title_div:
            # The title structure is complex, let's extract the key parts
            title_text = title_div.get_text()

            # Extract title number (e.g., "Title 68")
            title_match = re.search(r'Title (\d+[A-Z]?)\. (.+)', title_text)
            if title_match:
                metadata['title_number'] = title_match.group(1)
                metadata['title_name'] = title_match.group(2)

            # Extract chapter
            chapter_match = re.search(r'Chapter (\d+[A-Z]?) - (.+)', title_text)
            if chapter_match:
                metadata['chapter_number'] = chapter_match.group(1)
                metadata['chapter_name'] = chapter_match.group(2)

            # Extract article if present
            article_match = re.search(r'Article (?:Article )?(\d+[A-Z]?) - (.+)', title_text)
            if article_match:
                metadata['article_number'] = article_match.group(1)
                metadata['article_name'] = article_match.group(2)

            # Extract section
            section_match = re.search(r'Section\s+(\d+[A-Z]?) - (.+)', title_text)
            if section_match:
                metadata['section_number'] = section_match.group(1)
                metadata['section_name'] = section_match.group(2)

        # Extract statute number from title or navigation
        title_element = soup.find('title')
        if title_element:
            metadata['page_title'] = title_element.get_text().strip()

        # Extract from the statutes title bar
        title_bar = soup.find('div', id='statutes-title')
        if title_bar:
            metadata['title_bar'] = title_bar.get_text().strip()

        return metadata

    def extract_statute_content(self, soup):
        """Extract the actual statute text content"""
        content = {}

        # The main content appears to be between <!--BEGIN DOCUMENT--> and <!--END DOCUMENT-->
        html_text = str(soup)

        # Find document content using comments as markers
        begin_marker = "<!--BEGIN DOCUMENT-->"
        end_marker = "<!--END DOCUMENT-->"

        begin_idx = html_text.find(begin_marker)
        end_idx = html_text.find(end_marker)

        if begin_idx != -1 and end_idx != -1:
            # Extract the content between markers
            content_html = html_text[begin_idx + len(begin_marker):end_idx]
            content_soup = BeautifulSoup(content_html, 'html.parser')

            # Extract paragraphs
            paragraphs = content_soup.find_all('p')
            content['paragraphs'] = []

            for i, para in enumerate(paragraphs, 1):
                para_text = para.get_text().strip()
                if para_text:  # Skip empty paragraphs
                    content['paragraphs'].append({
                        'number': i,
                        'text': para_text
                    })

            # Get full text
            content['full_text'] = content_soup.get_text().strip()

        # Extract historical data if present
        historical_section = soup.find('b', string=re.compile(r'Historical Data'))
        if historical_section:
            # Find the next HR tag to get the historical content
            historical_content = ""
            current = historical_section.parent
            while current and current.name != 'hr':
                if hasattr(current, 'get_text'):
                    historical_content += current.get_text()
                current = current.next_sibling

            if historical_content:
                content['historical_data'] = historical_content.strip()

        return content

    def extract_navigation_links(self, soup):
        """Extract navigation links to related statutes"""
        links = {}

        # Extract from the statutes navigation bar
        nav_div = soup.find('div', id='statutes-navigation')
        if nav_div:
            nav_links = nav_div.find_all('a')
            for link in nav_links:
                if 'javascript:' in link.get('href', ''):
                    # These are JavaScript navigation functions
                    links[link.get_text().strip()] = link.get('href')

        # Extract citation links from the table of authority
        authority_table = soup.find('table')
        if authority_table:
            citation_links = []
            rows = authority_table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cells = row.find_all('td')
                if len(cells) >= 3:
                    cite_link = cells[1].find('a')
                    name_link = cells[2].find('a')
                    if cite_link and name_link:
                        citation_links.append({
                            'cite': cite_link.get_text().strip(),
                            'name': name_link.get_text().strip(),
                            'href': cite_link.get('href')
                        })

            links['citations'] = citation_links

        return links

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
            'navigation': self.extract_navigation_links(soup),
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        return result

    def scrape_title_index(self, title_number):
        """Scrape the index page for a title to find all sections"""
        url = f"{self.base_url}/applications/OCISWeb/index.asp?level=1&ftdb=STOKST{title_number}"
        logger.info(f"Scraping title index: {url}")

        html = self.get_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')

        # Find all statute links (this would need to be refined based on the actual index structure)
        statute_links = []
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href']
            if 'DeliverDocument.asp?CiteID=' in href:
                cite_id_match = re.search(r'CiteID=(\d+)', href)
                if cite_id_match:
                    cite_id = cite_id_match.group(1)
                    statute_links.append({
                        'cite_id': cite_id,
                        'text': link.get_text().strip(),
                        'url': urljoin(self.base_url, href)
                    })

        return statute_links

def test_refined_scraper():
    """Test the refined scraper on the sample statute"""
    scraper = RefinedOklahomaStatutesScraper()

    # Test with the known statute
    result = scraper.scrape_statute('440462')

    if result:
        print("=== REFINED SCRAPER RESULTS ===")
        print(f"Cite ID: {result['cite_id']}")
        print(f"URL: {result['url']}")

        print("\n=== METADATA ===")
        for key, value in result['metadata'].items():
            print(f"{key}: {value}")

        print("\n=== CONTENT ===")
        content = result['content']
        if 'paragraphs' in content:
            print(f"Found {len(content['paragraphs'])} paragraphs:")
            for para in content['paragraphs'][:3]:  # First 3 paragraphs
                print(f"  {para['number']}: {para['text'][:100]}...")

        if 'historical_data' in content:
            print(f"\nHistorical Data: {content['historical_data'][:200]}...")

        print("\n=== NAVIGATION LINKS ===")
        nav = result['navigation']
        for key, value in nav.items():
            if key == 'citations':
                print(f"{key}: {len(value)} citations found")
                for cite in value[:3]:  # First 3 citations
                    print(f"  {cite['cite']}: {cite['name']}")
            else:
                print(f"{key}: {value}")

        # Save to file
        with open('refined_statute_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to: refined_statute_result.json")
    else:
        print("Failed to scrape statute")

if __name__ == "__main__":
    test_refined_scraper()