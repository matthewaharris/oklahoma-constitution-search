#!/usr/bin/env python3
"""
Test HTML Parser - Parse OSCN statute and compare to database schema
"""
import json
from bs4 import BeautifulSoup
from pathlib import Path
import re

def parse_oscn_statute(html_file_path):
    """Parse an OSCN statute HTML file and extract all fields"""

    # Try multiple encodings
    for encoding in ['windows-1252', 'utf-8', 'latin-1']:
        try:
            with open(html_file_path, 'r', encoding=encoding) as f:
                html = f.read()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Could not decode HTML file with any supported encoding")

    soup = BeautifulSoup(html, 'html.parser')

    # Initialize data structure
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
        'title_bar': None,
        'citation_format': None,
        'main_text': None,
        'paragraphs': [],
        'definitions': [],
        'legislative_history': [],
        'citations': [],
        'superseded_documents': []
    }

    # Extract CiteID from URL in HTML (line 2)
    url_comment = str(soup)[:500]
    cite_match = re.search(r'CiteID=(\d+)', url_comment)
    if cite_match:
        parsed_data['cite_id'] = cite_match.group(1)
        parsed_data['url'] = f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_match.group(1)}"

    # Extract page title
    title_tag = soup.find('title')
    if title_tag:
        parsed_data['page_title'] = title_tag.get_text(strip=True)

    # Find the main content area
    main_content = soup.find('pre') or soup.find('div', id='oscn-content')

    if main_content:
        # Get full text
        parsed_data['main_text'] = main_content.get_text(strip=True)

        # Extract citation format (e.g., "10 O.S. § 7003-5.3")
        citation_pattern = re.search(r'(\d+)\s+O\.S\.\s+§\s+([\d\-\.A-Za-z]+)', parsed_data['main_text'])
        if citation_pattern:
            parsed_data['title_number'] = citation_pattern.group(1)
            parsed_data['section_number'] = citation_pattern.group(2)
            parsed_data['citation_format'] = f"{citation_pattern.group(1)} O.S. § {citation_pattern.group(2)}"

        # Extract section name from page title or first heading
        if parsed_data['page_title']:
            parsed_data['section_name'] = parsed_data['page_title']

        # Try to extract chapter/article info from text
        # Look for patterns like "CHAPTER 70" or "ARTICLE 3"
        chapter_match = re.search(r'CHAPTER\s+(\d+)', parsed_data['main_text'], re.IGNORECASE)
        if chapter_match:
            parsed_data['chapter_number'] = chapter_match.group(1)

        article_match = re.search(r'ARTICLE\s+(\d+)', parsed_data['main_text'], re.IGNORECASE)
        if article_match:
            parsed_data['article_number'] = article_match.group(1)

        # Extract title name (usually appears near the beginning)
        title_name_patterns = [
            r'TITLE\s+\d+[^\n]*\n([^\n]+)',
            r'(\w+(?:\s+\w+){1,5})\s+CODE',
        ]
        for pattern in title_name_patterns:
            match = re.search(pattern, parsed_data['main_text'])
            if match:
                parsed_data['title_name'] = match.group(1).strip()
                break

    # Look for legislative history section
    # Usually contains "Laws 1997, c. 1, § 1" type references
    if parsed_data['main_text']:
        history_pattern = re.findall(
            r'Laws\s+(\d{4}),\s+c\.\s+(\d+),\s+§\s+(\d+)',
            parsed_data['main_text']
        )
        for year, chapter, section in history_pattern:
            parsed_data['legislative_history'].append({
                'year': int(year),
                'bill_type': 'Laws',
                'bill_number': f"c. {chapter}",
                'details': f"Laws {year}, c. {chapter}, § {section}"
            })

    # Look for definitions section
    # Usually starts with "As used in this section:" or similar
    if parsed_data['main_text']:
        # Check for definition patterns
        definition_section = re.search(
            r'As used in this (?:section|act|chapter)[:\.](.+?)(?:\n\n|\Z)',
            parsed_data['main_text'],
            re.DOTALL | re.IGNORECASE
        )
        if definition_section:
            # Extract numbered/lettered definitions
            def_text = definition_section.group(1)
            # Pattern for definitions like: 1. "Term" means ...
            def_matches = re.findall(
                r'(\d+|[a-z])\.\s*["\']([^"\']+)["\']?\s+means?\s+([^;\.]+)',
                def_text,
                re.IGNORECASE
            )
            for def_num, term, definition in def_matches:
                parsed_data['definitions'].append({
                    'definition_number': def_num,
                    'term': term.strip(),
                    'definition': definition.strip()
                })

    # Look for citations/cross-references
    # Pattern: § 1234, or Title 10 § 1234
    citation_matches = re.findall(
        r'(?:Title\s+(\d+)\s+)?§\s+([\d\-\.A-Za-z]+)',
        parsed_data['main_text']
    )
    for title, section in citation_matches[:20]:  # Limit to first 20
        citation_text = f"§ {section}" if not title else f"Title {title} § {section}"
        parsed_data['citations'].append({
            'citation_text': citation_text,
            'cited_statute_cite_id': None  # Would need lookup
        })

    # Break text into paragraphs (basic splitting)
    if parsed_data['main_text']:
        paragraphs = [p.strip() for p in parsed_data['main_text'].split('\n\n') if p.strip()]
        for i, para in enumerate(paragraphs[:50], 1):  # Limit to first 50 paragraphs
            if len(para) > 20:  # Only substantive paragraphs
                parsed_data['paragraphs'].append({
                    'paragraph_number': i,
                    'text': para
                })

    return parsed_data

def compare_to_schema(parsed_data):
    """Compare parsed data to database schema and identify gaps"""

    schema_fields = {
        'statutes': [
            'cite_id', 'url', 'title_number', 'title_name', 'chapter_number',
            'chapter_name', 'article_number', 'article_name', 'section_number',
            'section_name', 'page_title', 'title_bar', 'citation_format', 'main_text'
        ],
        'statute_paragraphs': ['paragraph_number', 'text'],
        'statute_definitions': ['definition_number', 'term', 'definition'],
        'legislative_history': ['year', 'bill_type', 'bill_number', 'details'],
        'statute_citations': ['cited_statute_cite_id', 'citation_text']
    }

    analysis = {
        'statutes_fields': {},
        'related_tables': {
            'paragraphs': len(parsed_data['paragraphs']),
            'definitions': len(parsed_data['definitions']),
            'legislative_history': len(parsed_data['legislative_history']),
            'citations': len(parsed_data['citations'])
        },
        'null_fields': [],
        'populated_fields': []
    }

    # Check which statutes table fields are populated
    for field in schema_fields['statutes']:
        value = parsed_data.get(field)
        if value is None or value == '':
            analysis['null_fields'].append(field)
            analysis['statutes_fields'][field] = None
        else:
            analysis['populated_fields'].append(field)
            # Truncate long values for display
            if isinstance(value, str) and len(value) > 100:
                analysis['statutes_fields'][field] = value[:100] + '...'
            else:
                analysis['statutes_fields'][field] = value

    return analysis

def main():
    print("="*80)
    print("OSCN Statute Parser Test")
    print("="*80)

    # Parse the HTML file
    html_file = Path('temp/Statewide Centralized Hotline for Reporting Child Abuse or Neglect - Hotline Requirements - Reporting Abuse or Neglect - Retaliation by Employer - Violations.html')

    if not html_file.exists():
        print(f"[ERROR] File not found: {html_file}")
        return

    print(f"\nParsing: {html_file.name}")
    print("-"*80)

    parsed_data = parse_oscn_statute(html_file)

    # Save full parsed data to JSON
    output_file = 'parsed_statute_test.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Full parsed data saved to: {output_file}")

    # Compare to schema
    print("\n" + "="*80)
    print("SCHEMA COMPARISON")
    print("="*80)

    analysis = compare_to_schema(parsed_data)

    print("\n## STATUTES TABLE FIELDS ##")
    print(f"\nPopulated Fields ({len(analysis['populated_fields'])} of 14):")
    for field in analysis['populated_fields']:
        value = analysis['statutes_fields'][field]
        print(f"  ✓ {field}: {value}")

    print(f"\nNULL Fields ({len(analysis['null_fields'])} of 14):")
    for field in analysis['null_fields']:
        print(f"  ✗ {field}: NULL")

    print("\n## RELATED TABLES ##")
    for table, count in analysis['related_tables'].items():
        status = "✓" if count > 0 else "✗"
        print(f"  {status} {table}: {count} records")

    # Show sample data
    print("\n" + "="*80)
    print("SAMPLE DATA")
    print("="*80)

    if parsed_data['paragraphs']:
        print(f"\nFirst Paragraph:")
        print(f"  {parsed_data['paragraphs'][0]['text'][:200]}...")

    if parsed_data['definitions']:
        print(f"\nDefinitions Found: {len(parsed_data['definitions'])}")
        for defn in parsed_data['definitions'][:3]:
            print(f"  {defn['definition_number']}. '{defn['term']}': {defn['definition'][:100]}...")

    if parsed_data['legislative_history']:
        print(f"\nLegislative History: {len(parsed_data['legislative_history'])} entries")
        for hist in parsed_data['legislative_history'][:3]:
            print(f"  - {hist['details']}")

    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    print("\nIssues to Address:")
    if 'title_name' in analysis['null_fields']:
        print("  1. title_name is NULL - need better extraction logic")
    if 'chapter_name' in analysis['null_fields']:
        print("  2. chapter_name is NULL - may not be in HTML")
    if 'article_name' in analysis['null_fields']:
        print("  3. article_name is NULL - may not be in HTML")
    if 'title_bar' in analysis['null_fields']:
        print("  4. title_bar is NULL - check what this field should contain")

    print("\nRecommendations:")
    print("  - Consider removing NULL-only fields from schema (title_bar, chapter_name, article_name)")
    print("  - Improve title_name extraction logic")
    print("  - Consider making some fields optional in database constraints")
    print("  - Use full_json JSONB field to store complete parsed data")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
