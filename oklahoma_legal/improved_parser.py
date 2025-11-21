#!/usr/bin/env python3
"""
Improved OSCN Statute Parser
Extracts all available data including legislative history
"""
import json
from bs4 import BeautifulSoup
from pathlib import Path
import re
from oklahoma_titles_lookup import get_title_name

def parse_legislative_history(text: str):
    """Parse legislative history from Historical Data section"""
    history_entries = []

    # Look for "Historical Data" or "History" section
    history_section = re.search(
        r'(?:Historical Data|History)[:\s]*(.+?)(?:Citationizer|$)',
        text,
        re.DOTALL | re.IGNORECASE
    )

    if not history_section:
        return history_entries

    history_text = history_section.group(1)

    # Pattern for legislative entries:
    # "Laws 1997, c. 1, § 1, emerg. eff. April 28, 1997"
    # "Amended by Laws 2025, HB 1565, c. 26, § 1, eff. November 1, 2025"
    patterns = [
        # Full pattern with bill type
        r'(?:Amended by |Renumbered from |Added by |Repealed by )?Laws\s+(\d{4}),\s+(HB|SB)\s+(\d+),\s+c\.\s+(\d+),\s+§\s+([\d\w]+)(?:,\s+(.+?))?(?=(?:;|Laws|\Z|Amended|Renumbered|Added|Repealed))',
        # Pattern without bill type
        r'(?:Amended by |Renumbered from |Added by |Repealed by )?Laws\s+(\d{4}),\s+c\.\s+(\d+),\s+§\s+([\d\w]+)(?:,\s+(.+?))?(?=(?:;|Laws|\Z|Amended|Renumbered|Added|Repealed))',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, history_text, re.DOTALL)
        for match in matches:
            groups = match.groups()

            if len(groups) == 6:  # Pattern with bill type
                year, bill_type, bill_num, chapter, section, rest = groups
                entry = {
                    'year': int(year),
                    'bill_type': bill_type,
                    'bill_number': bill_num,
                    'chapter': chapter,
                    'section': section,
                    'details': match.group(0).strip(),
                    'effective_date': None
                }
            else:  # Pattern without bill type
                year, chapter, section, rest = groups
                entry = {
                    'year': int(year),
                    'bill_type': 'Laws',
                    'bill_number': None,
                    'chapter': chapter,
                    'section': section,
                    'details': match.group(0).strip(),
                    'effective_date': None
                }

            # Extract effective date from rest
            if rest:
                # Look for effective date patterns
                eff_patterns = [
                    r'eff\.\s+([^,;]+)',
                    r'emerg\.\s+eff\.\s+([^,;]+)',
                    r'effective\s+([^,;]+)'
                ]
                for eff_pattern in eff_patterns:
                    eff_match = re.search(eff_pattern, rest, re.IGNORECASE)
                    if eff_match:
                        entry['effective_date'] = eff_match.group(1).strip()
                        break

            history_entries.append(entry)

    return history_entries

def parse_definitions(text: str):
    """Improved definition parser with multiple patterns"""
    definitions = []

    # Pattern 1: "As used in this section/act/chapter:"
    definition_patterns = [
        r'As used in this (?:section|act|chapter|title)[:\.](.+?)(?:(?:\n\n)|(?:[A-Z]\.\s+\d)|$)',
        r'For purposes of this (?:section|act|chapter|title)[:\.](.+?)(?:(?:\n\n)|(?:[A-Z]\.\s+\d)|$)',
        r'Definitions[:\.](.+?)(?:(?:\n\n)|(?:[A-Z]\.\s+\d)|$)',
    ]

    for pattern in definition_patterns:
        def_section = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if def_section:
            def_text = def_section.group(1)

            # Extract numbered/lettered definitions
            # Pattern: 1. "Term" means definition
            def_matches = re.findall(
                r'(\d+|[a-z])\.\s*["\']([^"\']+)["\']?\s+(?:means?|shall mean|refers to)\s+([^;\.]+)',
                def_text,
                re.IGNORECASE
            )
            for def_num, term, definition in def_matches:
                definitions.append({
                    'definition_number': def_num.strip(),
                    'term': term.strip(),
                    'definition': definition.strip()
                })
            break

    return definitions

def parse_oscn_statute_improved(html_file_path):
    """Improved parser with legislative history and title lookup"""

    # Try multiple encodings
    for encoding in ['windows-1252', 'utf-8', 'latin-1']:
        try:
            with open(html_file_path, 'r', encoding=encoding) as f:
                html = f.read()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Could not decode HTML file")

    soup = BeautifulSoup(html, 'html.parser')

    parsed_data = {
        'cite_id': None,
        'url': None,
        'title_number': None,
        'title_name': None,
        'chapter_number': None,
        'chapter_name': None,
        'article_number': None,
        'article_name': None,
        'section_number': None,
        'section_name': None,
        'page_title': None,
        'citation_format': None,
        'main_text': None,
        'paragraphs': [],
        'definitions': [],
        'legislative_history': [],
        'citations': [],
        'superseded_documents': []
    }

    # Extract CiteID
    url_comment = str(soup)[:500]
    cite_match = re.search(r'CiteID=(\d+)', url_comment)
    if cite_match:
        parsed_data['cite_id'] = cite_match.group(1)
        parsed_data['url'] = f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_match.group(1)}"

    # Extract page title
    title_tag = soup.find('title')
    if title_tag:
        parsed_data['page_title'] = title_tag.get_text(strip=True)
        parsed_data['section_name'] = parsed_data['page_title']

    # Find main content
    main_content = soup.find('pre') or soup.find('div', id='oscn-content')

    if main_content:
        parsed_data['main_text'] = main_content.get_text(strip=True)

        # Extract citation format and parse structure
        # Try multiple citation patterns
        citation_patterns = [
            r'(\d+[A-Z]?)\s+O\.S\.\s+§\s+([\d\-\.A-Za-z]+)',  # Standard: "10A O.S. § 1-2-101"
            r'Cite as:\s*(\d+[A-Z]?)\s+O\.S\.\s+§\s+([\d\-\.A-Za-z]+)',
        ]

        for pattern in citation_patterns:
            citation_match = re.search(pattern, parsed_data['main_text'])
            if citation_match:
                parsed_data['title_number'] = citation_match.group(1)
                parsed_data['section_number'] = citation_match.group(2)
                parsed_data['citation_format'] = f"{citation_match.group(1)} O.S. § {citation_match.group(2)}"

                # Lookup title name
                parsed_data['title_name'] = get_title_name(parsed_data['title_number'])
                break

        # Extract Article and Chapter info
        # Pattern: "Article 1 - Oklahoma Children's Code"
        article_pattern = re.search(
            r'Article\s+(\d+)\s*-\s*([^\n]+)',
            parsed_data['main_text'],
            re.IGNORECASE
        )
        if article_pattern:
            parsed_data['article_number'] = article_pattern.group(1)
            parsed_data['article_name'] = article_pattern.group(2).strip()

        # Pattern: "Chapter 2 - Reporting and Investigations"
        chapter_pattern = re.search(
            r'(?:Article\s+)?Chapter\s+(\d+)\s*-\s*([^\n]+)',
            parsed_data['main_text'],
            re.IGNORECASE
        )
        if chapter_pattern:
            parsed_data['chapter_number'] = chapter_pattern.group(1)
            parsed_data['chapter_name'] = chapter_pattern.group(2).strip()

        # Parse legislative history (IMPROVED)
        parsed_data['legislative_history'] = parse_legislative_history(parsed_data['main_text'])

        # Parse definitions (IMPROVED)
        parsed_data['definitions'] = parse_definitions(parsed_data['main_text'])

        # Extract citations/cross-references
        citation_matches = re.findall(
            r'(?:Title\s+(\d+[A-Z]?)\s+)?§\s+([\d\-\.A-Za-z]+)',
            parsed_data['main_text']
        )
        seen_citations = set()
        for title, section in citation_matches[:50]:  # Limit to first 50
            citation_text = f"§ {section}" if not title else f"Title {title} § {section}"
            if citation_text not in seen_citations:
                parsed_data['citations'].append({
                    'citation_text': citation_text,
                    'cited_statute_cite_id': None,
                    'title_number': title if title else None
                })
                seen_citations.add(citation_text)

        # Break text into paragraphs
        if parsed_data['main_text']:
            # Split by double newline or numbered sections
            paragraphs = re.split(r'\n\n+|(?=\n[A-Z]\.\s+\d)', parsed_data['main_text'])
            para_num = 1
            for para in paragraphs:
                para = para.strip()
                if len(para) > 20 and para_num <= 100:  # Limit to 100 paragraphs
                    parsed_data['paragraphs'].append({
                        'paragraph_number': para_num,
                        'text': para
                    })
                    para_num += 1

    return parsed_data

def main():
    print("="*80)
    print("IMPROVED OSCN Statute Parser Test")
    print("="*80)

    html_file = Path('temp/Statewide Centralized Hotline for Reporting Child Abuse or Neglect - Hotline Requirements - Reporting Abuse or Neglect - Retaliation by Employer - Violations.html')

    if not html_file.exists():
        print(f"[ERROR] File not found: {html_file}")
        return

    print(f"\nParsing: {html_file.name[:60]}...")
    parsed_data = parse_oscn_statute_improved(html_file)

    # Save to JSON
    output_file = 'parsed_statute_improved.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved to: {output_file}")

    print("\n" + "="*80)
    print("PARSING RESULTS")
    print("="*80)

    # Show key fields
    print("\n## MAIN FIELDS ##")
    print(f"  CiteID: {parsed_data['cite_id']}")
    print(f"  URL: {parsed_data['url']}")
    print(f"  Citation: {parsed_data['citation_format']}")
    print(f"  Title Number: {parsed_data['title_number']}")
    print(f"  Title Name: {parsed_data['title_name']}")  # NEW!
    print(f"  Chapter: {parsed_data['chapter_number']} - {parsed_data['chapter_name']}")  # IMPROVED!
    print(f"  Article: {parsed_data['article_number']} - {parsed_data['article_name']}")  # IMPROVED!
    print(f"  Section: {parsed_data['section_number']}")

    # Show counts
    print("\n## DATA EXTRACTED ##")
    print(f"  Paragraphs: {len(parsed_data['paragraphs'])}")
    print(f"  Definitions: {len(parsed_data['definitions'])}")
    print(f"  Legislative History: {len(parsed_data['legislative_history'])}")  # NEW!
    print(f"  Citations: {len(parsed_data['citations'])}")

    # Show legislative history samples
    if parsed_data['legislative_history']:
        print("\n## LEGISLATIVE HISTORY (First 5) ##")
        for i, hist in enumerate(parsed_data['legislative_history'][:5], 1):
            print(f"  {i}. {hist['year']} - {hist['bill_type']} {hist.get('bill_number', 'N/A')}")
            print(f"     Effective: {hist['effective_date']}")
            print(f"     Details: {hist['details'][:80]}...")

    # Show field coverage
    print("\n## SCHEMA COVERAGE ##")
    fields = ['cite_id', 'url', 'title_number', 'title_name', 'chapter_number',
              'chapter_name', 'article_number', 'article_name', 'section_number',
              'section_name', 'page_title', 'citation_format', 'main_text']

    populated = sum(1 for f in fields if parsed_data.get(f))
    print(f"  Populated: {populated}/{len(fields)} ({populated/len(fields)*100:.1f}%)")

    null_fields = [f for f in fields if not parsed_data.get(f)]
    if null_fields:
        print(f"  NULL fields: {', '.join(null_fields)}")

    print("\n" + "="*80)
    print("IMPROVEMENTS FROM PREVIOUS PARSER:")
    print("="*80)
    print("  + Title name now populated via lookup table")
    print("  + Chapter name extracted from HTML")
    print("  + Article name extracted from HTML")
    print(f"  + Legislative history: {len(parsed_data['legislative_history'])} entries extracted")
    print(f"  + Improved definition parsing")
    print(f"\nSchema coverage improved from 71% to {populated/len(fields)*100:.1f}%")

if __name__ == "__main__":
    main()
