#!/usr/bin/env python3
"""
Oklahoma Statutes Scraper for OSCN (Oklahoma State Courts Network)
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OklahomaStatutesScraper:
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

    def explore_main_page(self):
        """Explore the main statutes page to understand structure"""
        main_url = f"{self.base_url}/applications/oscn/DeliverDocument.asp?CiteID=440462"
        logger.info(f"Exploring main page: {main_url}")

        html = self.get_page(main_url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Save the raw HTML for analysis
        with open('oscn_main_page.html', 'w', encoding='utf-8') as f:
            f.write(html)

        print("=== PAGE TITLE ===")
        print(soup.title.text if soup.title else "No title found")

        print("\n=== ALL LINKS ===")
        links = soup.find_all('a', href=True)
        for i, link in enumerate(links[:20]):  # First 20 links
            print(f"{i+1}. {link.text.strip()[:100]} -> {link['href']}")

        print(f"\nTotal links found: {len(links)}")

        print("\n=== POSSIBLE TITLE SELECTORS ===")
        # Look for potential title patterns
        for tag in ['h1', 'h2', 'h3', 'title']:
            elements = soup.find_all(tag)
            if elements:
                print(f"{tag.upper()}: {[elem.text.strip() for elem in elements[:5]]}")

        print("\n=== DIV CLASSES ===")
        divs = soup.find_all('div', class_=True)
        classes = set()
        for div in divs:
            if isinstance(div.get('class'), list):
                classes.update(div['class'])
            else:
                classes.add(div.get('class'))
        print("Found classes:", sorted(list(classes))[:20])

        return soup

    def test_selectors(self, soup):
        """Test various selector patterns"""
        print("\n=== TESTING SELECTORS ===")

        # Common patterns to test
        selectors = [
            "div.main-content",
            "div.content",
            "div.statute-text",
            ".statute",
            ".law-text",
            "div[class*='text']",
            "div[class*='content']",
            "div[class*='main']",
            "table",
            "pre",
            "p"
        ]

        for selector in selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    print(f"{selector}: {len(elements)} elements found")
                    # Show first element text preview
                    text = elements[0].get_text().strip()
                    print(f"  Preview: {text[:100]}...")
                else:
                    print(f"{selector}: No elements found")
            except Exception as e:
                print(f"{selector}: Error - {e}")

    def find_statute_links(self, soup):
        """Find links that look like statute sections"""
        print("\n=== STATUTE LINKS ANALYSIS ===")

        links = soup.find_all('a', href=True)
        statute_patterns = [
            r'\d+[A-Z]?-\d+',  # 11-103, 15A-401
            r'§\s*\d+',        # § 123
            r'Section\s+\d+',   # Section 123
            r'\d+\.\d+',       # 11.5
        ]

        statute_links = []
        for link in links:
            text = link.get_text().strip()
            href = link['href']

            # Check if text matches statute patterns
            for pattern in statute_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    statute_links.append({
                        'text': text,
                        'href': href,
                        'pattern': pattern
                    })
                    break

        print(f"Found {len(statute_links)} potential statute links")
        for link in statute_links[:10]:
            print(f"  {link['text']} -> {link['href']}")

        return statute_links

def main():
    scraper = OklahomaStatutesScraper()

    print("Starting Oklahoma Statutes scraper exploration...")

    # Explore main page
    soup = scraper.explore_main_page()
    if soup:
        # Test selectors
        scraper.test_selectors(soup)

        # Find statute links
        scraper.find_statute_links(soup)

        print("\nExploration complete. Check oscn_main_page.html for the raw HTML.")
    else:
        print("Failed to fetch main page")

if __name__ == "__main__":
    main()