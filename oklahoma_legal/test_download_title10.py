#!/usr/bin/env python3
"""Test download - only first 20 statutes from Title 10"""

import json
import sys
from slow_downloader import SlowStatuteDownloader

print("TEST DOWNLOAD: First 20 statutes from Title 10", flush=True)
print("="*60, flush=True)
print("This will take about 3-4 minutes", flush=True)
print("="*60, flush=True)
print(flush=True)

# Load Title 10 URLs
with open('title_10_urls.json', 'r') as f:
    data = json.load(f)
    urls = data.get('urls', [])

print(f"Loaded {len(urls)} total URLs", flush=True)

# Initialize downloader
downloader = SlowStatuteDownloader(delay_seconds=10)

# Take only first 20 for testing
test_urls = urls[:20]

print(f"Testing with first {len(test_urls)} statutes...", flush=True)
print(flush=True)

# Download each statute
success_count = 0
failure_count = 0

for i, statute_info in enumerate(test_urls, 1):
    cite_id = statute_info['cite_id']
    url = statute_info['url']
    title_number = statute_info['title_number']

    print(f"[{i}/{len(test_urls)}] Downloading cite_id: {cite_id}", flush=True)

    if downloader.download_statute(url, cite_id, title_number):
        success_count += 1
        print(f"  SUCCESS - Downloaded {cite_id}", flush=True)
    else:
        failure_count += 1
        print(f"  FAILED - {cite_id}", flush=True)

    print(flush=True)

# Final save
downloader.save_progress()

print(f"{'='*60}", flush=True)
print("Test Download Complete!", flush=True)
print(f"{'='*60}", flush=True)
print(f"Successfully downloaded: {success_count}", flush=True)
print(f"Failed: {failure_count}", flush=True)
print(f"Output directory: {downloader.output_dir.absolute()}", flush=True)
print(flush=True)
print("If this test succeeded, run download_title10.py for the full 1,345 statutes", flush=True)
