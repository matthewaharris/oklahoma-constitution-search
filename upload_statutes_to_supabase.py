#!/usr/bin/env python3
"""
Upload processed statute data to Supabase
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import json
import re

# Import supabase
try:
    from supabase import create_client, Client
except ImportError:
    print("[ERROR] Supabase library not installed")
    print("Install with: pip install supabase")
    sys.exit(1)

# Import config
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import SUPABASE_URL, SUPABASE_KEY
else:
    try:
        from config import SUPABASE_URL, SUPABASE_KEY
    except ImportError:
        from config_production import SUPABASE_URL, SUPABASE_KEY

print("Uploading Oklahoma Statutes to Supabase")
print("=" * 60)

# Initialize Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[OK] Connected to Supabase")
except Exception as e:
    print(f"[ERROR] Failed to connect to Supabase: {e}")
    sys.exit(1)

# Find all HTML files
html_dir = Path('statute_html/title_10')
if not html_dir.exists():
    print(f"[ERROR] Directory not found: {html_dir}")
    sys.exit(1)

html_files = list(html_dir.glob('*.html'))
print(f"Found {len(html_files)} HTML files to process")
print()

# Process each file
success_count = 0
failure_count = 0
batch = []
batch_size = 50

for i, html_path in enumerate(html_files, 1):
    try:
        # Read HTML
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')

        # Load metadata
        meta_path = html_path.with_suffix('.meta.json')
        metadata = {}
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                metadata = json.load(f)

        # Extract section name
        title_tag = soup.find('title')
        section_name = title_tag.get_text(strip=True) if title_tag else "Untitled"

        h1_tag = soup.find('h1')
        if h1_tag:
            section_name = h1_tag.get_text(strip=True)

        # Extract text
        main_content = soup.find('div', class_='main') or soup.find('div', id='content')
        if main_content:
            text_content = main_content.get_text(separator='\n', strip=True)
        else:
            paragraphs = soup.find_all('p')
            text_content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])

        # Clean text
        text_content = re.sub(r'\n{3,}', '\n\n', text_content).strip()

        # Extract section number
        section_match = re.search(r'Section\s+(\d+[A-Za-z]?[\-\d\.]*)', section_name, re.IGNORECASE)
        section_number = section_match.group(1) if section_match else ""

        # Get title number
        title_number = metadata.get('title_number', 10)

        # Prepare record for Supabase (matching statutes table schema)
        cite_id = metadata.get('cite_id', html_path.stem.replace('cite_', ''))

        record = {
            'cite_id': cite_id,
            'url': metadata.get('url', ''),
            'title_number': str(title_number),
            'title_name': f"Title {title_number}",
            'chapter_number': None,
            'chapter_name': None,
            'article_number': None,
            'article_name': None,
            'section_number': section_number,
            'section_name': section_name,
            'page_title': section_name,
            'title_bar': None,
            'citation_format': None,
            'main_text': text_content,
            'full_json': {
                'cite_id': cite_id,
                'title_number': title_number,
                'section_name': section_name,
                'section_number': section_number,
                'text': text_content,
                'url': metadata.get('url', ''),
                'downloaded_at': metadata.get('downloaded_at', ''),
                'processed_at': datetime.now().isoformat()
            },
            'scraper_version': '1.0'
        }

        batch.append(record)

        # Upload batch when full
        if len(batch) >= batch_size:
            try:
                result = supabase.table('statutes').insert(batch).execute()
                success_count += len(batch)
                print(f"[{i}/{len(html_files)}] Uploaded batch of {len(batch)} records")
                batch = []
            except Exception as e:
                print(f"[ERROR] Batch upload failed: {e}")
                failure_count += len(batch)
                batch = []

    except Exception as e:
        print(f"[ERROR] Failed to process {html_path.name}: {e}")
        failure_count += 1

# Upload remaining batch
if batch:
    try:
        result = supabase.table('statutes').insert(batch).execute()
        success_count += len(batch)
        print(f"Uploaded final batch of {len(batch)} records")
    except Exception as e:
        print(f"[ERROR] Final batch upload failed: {e}")
        failure_count += len(batch)

print("\n" + "=" * 60)
print("Upload Complete!")
print("=" * 60)
print(f"Successfully uploaded: {success_count}")
print(f"Failed: {failure_count}")
print(f"\nYou can now query statutes from Supabase!")
print("=" * 60)
