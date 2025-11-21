"""
Robust HTML parser for Oklahoma Constitution and Statutes
Extracts structured data from OSCN HTML files
"""

from bs4 import BeautifulSoup
from pathlib import Path
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class OklahomaDocumentParser:
    """Parse Oklahoma legal documents from OSCN HTML files"""

    def __init__(self):
        self.scraper_version = "2.0"

    def parse_html_file(self, html_path: Path) -> Dict:
        """
        Parse an OSCN HTML file and extract structured data

        Args:
            html_path: Path to HTML file

        Returns:
            Dictionary with extracted data
        """
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract cite_id from filename
        cite_id = html_path.stem.replace('CiteID_', '')

        # Determine document type from dbcode
        document_type = self._extract_document_type(html_content)

        # Extract basic metadata
        page_title = self._extract_page_title(soup)
        url = f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}"

        # Extract main content
        main_text = self._extract_main_text(soup)

        # Extract citation format
        citation_format = self._extract_citation_format(soup, main_text)

        # Extract title/article information based on document type
        if document_type == 'constitution':
            metadata = self._extract_constitution_metadata(soup, main_text, page_title)
        else:
            metadata = self._extract_statute_metadata(soup, main_text, page_title)

        # Combine all data
        result = {
            'cite_id': cite_id,
            'url': url,
            'document_type': document_type,
            'page_title': page_title,
            'citation_format': citation_format,
            'main_text': main_text,
            **metadata,
            'scraped_at': datetime.now().isoformat(),
            'scraper_version': self.scraper_version
        }

        return result

    def _extract_document_type(self, html_content: str) -> str:
        """Determine if this is a statute or constitution document"""
        if 'dbcode=STOKCN' in html_content or 'dbCode=STOKCN' in html_content:
            return 'constitution'
        return 'statute'

    def _extract_page_title(self, soup: BeautifulSoup) -> str:
        """Extract the page title"""
        # Try <title> tag first
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            # Remove "OSCN Found Document:" prefix if present
            title = re.sub(r'^OSCN Found Document:\s*', '', title)
            return title

        return ''

    def _extract_main_text(self, soup: BeautifulSoup) -> str:
        """Extract the main statute/constitution text"""
        # Find the main content area
        # OSCN typically has content in <pre> tags or specific divs

        # Try <pre> tags first (common in OSCN)
        pre_tags = soup.find_all('pre')
        if pre_tags:
            text_parts = []
            for pre in pre_tags:
                text = pre.get_text().strip()
                if len(text) > 100:  # Only substantial content
                    text_parts.append(text)
            if text_parts:
                return '\n\n'.join(text_parts)

        # Try finding content div
        content_div = soup.find('div', {'id': 'oscn-content'})
        if content_div:
            # Remove script and style tags
            for tag in content_div.find_all(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            return content_div.get_text().strip()

        # Fallback: get all text
        return soup.get_text().strip()

    def _extract_citation_format(self, soup: BeautifulSoup, main_text: str) -> Optional[str]:
        """Extract the citation format (e.g., '21 O.S. § 1-101')"""
        # Look for common citation patterns in the text
        patterns = [
            r'(\d+)\s+O\.S\.\s*§\s*[\d\-\.]+[a-z]*',  # "21 O.S. § 1-101"
            r'Okla\.\s*Const\.\s*[Aa]rt\.\s*[IVXLCDM]+,\s*§\s*\d+',  # "Okla. Const. Art. X, § 1"
            r'Article\s+[IVXLCDM]+,\s*Section\s+\d+',  # "Article X, Section 1"
        ]

        for pattern in patterns:
            match = re.search(pattern, main_text[:2000])  # Search first 2000 chars
            if match:
                return match.group(0)

        return None

    def _extract_statute_metadata(self, soup: BeautifulSoup, main_text: str, page_title: str) -> Dict:
        """Extract metadata specific to statutes"""
        metadata = {
            'title_number': None,
            'title_name': None,
            'chapter_number': None,
            'chapter_name': None,
            'section_number': None,
            'section_name': None,
        }

        # Extract title number from various sources
        # Pattern: "Title 21" or "21 O.S."
        title_match = re.search(r'Title\s+(\d+)', main_text[:1000])
        if not title_match:
            title_match = re.search(r'(\d+)\s+O\.S\.', main_text[:1000])
        if title_match:
            metadata['title_number'] = title_match.group(1)

        # Extract section number
        # Pattern: "§ 1-101" or "Section 1-101"
        section_match = re.search(r'§\s*([\d\-\.]+[a-z]*)', main_text[:1000])
        if not section_match:
            section_match = re.search(r'Section\s+([\d\-\.]+[a-z]*)', main_text[:1000])
        if section_match:
            metadata['section_number'] = section_match.group(1)

        # Use page title as section name if available
        if page_title:
            metadata['section_name'] = page_title

        return metadata

    def _extract_constitution_metadata(self, soup: BeautifulSoup, main_text: str, page_title: str) -> Dict:
        """Extract metadata specific to constitution"""
        metadata = {
            'article_number': None,
            'article_name': None,
            'section_number': None,
            'section_name': None,
        }

        # Extract article number
        # Pattern: "Article X" or "Art. X"
        article_match = re.search(r'Article\s+([IVXLCDM]+)', main_text[:1000])
        if not article_match:
            article_match = re.search(r'Art\.\s*([IVXLCDM]+)', main_text[:1000])
        if article_match:
            metadata['article_number'] = article_match.group(1)

        # Extract section number
        section_match = re.search(r'§\s*(\d+[a-z]*)', main_text[:1000])
        if not section_match:
            section_match = re.search(r'Section\s+(\d+[a-z]*)', main_text[:1000])
        if section_match:
            metadata['section_number'] = section_match.group(1)

        # Use page title as section name or article name
        if page_title:
            if metadata['section_number']:
                metadata['section_name'] = page_title
            else:
                metadata['article_name'] = page_title

        return metadata


# Test the parser
if __name__ == "__main__":
    parser = OklahomaDocumentParser()

    # Test with a statute file
    statute_file = Path("html_files/statutes/title_10/CiteID_103839.html")
    if statute_file.exists():
        print("Testing Statute Parser:")
        print("=" * 70)
        result = parser.parse_html_file(statute_file)
        print(f"CiteID: {result['cite_id']}")
        print(f"Type: {result['document_type']}")
        print(f"Title: {result.get('title_number', 'N/A')}")
        print(f"Section: {result.get('section_number', 'N/A')}")
        print(f"Page Title: {result['page_title'][:80]}")
        print(f"Text length: {len(result['main_text'])} chars")
        print()

    # Test with a constitution file
    const_file = Path("html_files/constitution/CiteID_434355.html")
    if const_file.exists():
        print("Testing Constitution Parser:")
        print("=" * 70)
        result = parser.parse_html_file(const_file)
        print(f"CiteID: {result['cite_id']}")
        print(f"Type: {result['document_type']}")
        print(f"Article: {result.get('article_number', 'N/A')}")
        print(f"Section: {result.get('section_number', 'N/A')}")
        print(f"Page Title: {result['page_title'][:80]}")
        print(f"Text length: {len(result['main_text'])} chars")
