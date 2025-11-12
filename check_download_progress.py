#!/usr/bin/env python3
"""
Check download progress for Title 10
"""

import os
import json
from pathlib import Path
from datetime import datetime

print("Title 10 Download Progress Monitor")
print("=" * 60)

# Count HTML files
html_dir = Path('statute_html/title_10')
if html_dir.exists():
    html_files = list(html_dir.glob('*.html'))
    total_downloaded = len(html_files)
else:
    total_downloaded = 0

# Load URL count
try:
    with open('title_10_urls.json', 'r') as f:
        data = json.load(f)
        total_urls = len(data.get('urls', []))
except:
    total_urls = 1345  # Known count

# Calculate progress
percent_complete = (total_downloaded / total_urls) * 100
remaining = total_urls - total_downloaded

# Estimate time remaining (10 seconds per statute)
seconds_remaining = remaining * 10
hours_remaining = seconds_remaining / 3600
minutes_remaining = (seconds_remaining % 3600) / 60

print(f"\nProgress: {total_downloaded:,} / {total_urls:,} statutes")
print(f"Percentage: {percent_complete:.1f}%")
print(f"Remaining: {remaining:,} statutes")
print(f"Estimated time: {int(hours_remaining)}h {int(minutes_remaining)}m")

# Show recent downloads
if html_dir.exists() and html_files:
    print(f"\nMost recent downloads:")
    recent = sorted(html_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
    for f in recent:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name}: {size_kb:.1f} KB - {mtime.strftime('%H:%M:%S')}")

# Check log file
log_file = Path('download_title10_full.log')
if log_file.exists():
    print(f"\nLog file: {log_file} ({log_file.stat().st_size / 1024:.1f} KB)")
    print("Last 5 lines:")
    with open(log_file, 'r') as f:
        lines = f.readlines()
        for line in lines[-5:]:
            print(f"  {line.rstrip()}")

# Check progress file
progress_file = Path('download_progress.json')
if progress_file.exists():
    try:
        with open(progress_file, 'r') as f:
            progress = json.load(f)
            print(f"\nProgress saved at: {progress.get('last_updated', 'Unknown')}")
            print(f"Tracked in progress file: {progress.get('count', 0):,}")
    except:
        pass

print("\n" + "=" * 60)
print("To check again, run: python check_download_progress.py")
print("To view live log: tail -f download_title10_full.log")
print("=" * 60)
