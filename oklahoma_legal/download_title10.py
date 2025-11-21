#!/usr/bin/env python3
"""Download HTML files for Title 10"""

import json
from slow_downloader import SlowStatuteDownloader

print("Downloading Title 10 HTML files")
print("="*60)
print("This will download 1,345 statutes with 10-second delays")
print("Estimated time: 3-4 hours")
print("You can interrupt with Ctrl+C and resume later")
print("="*60)
print()

# Load Title 10 URLs
with open('title_10_urls.json', 'r') as f:
    data = json.load(f)
    urls = data.get('urls', [])

print(f"Loaded {len(urls)} URLs")

# Initialize downloader
downloader = SlowStatuteDownloader(delay_seconds=10)

# Filter to only Title 10
title_10_urls = [u for u in urls if u['title_number'] == 10]

print(f"Starting download of {len(title_10_urls)} Title 10 statutes...")
print()

# Download each statute
success_count = 0
failure_count = 0

for i, statute_info in enumerate(title_10_urls, 1):
    cite_id = statute_info['cite_id']
    url = statute_info['url']
    title_number = statute_info['title_number']

    print(f"[{i}/{len(title_10_urls)}] Processing cite_id: {cite_id}")

    if downloader.download_statute(url, cite_id, title_number):
        success_count += 1
    else:
        failure_count += 1

    # Save progress every 10 downloads
    if i % 10 == 0:
        downloader.save_progress()
        print(f"\nProgress saved: {len(downloader.downloaded)} downloaded\n")

# Final save
downloader.save_progress()

print(f"\n{'='*60}")
print("Download Complete!")
print(f"{'='*60}")
print(f"Successfully downloaded: {success_count}")
print(f"Failed: {failure_count}")
print(f"Total in database: {len(downloader.downloaded)}")
print(f"Output directory: {downloader.output_dir.absolute()}")
