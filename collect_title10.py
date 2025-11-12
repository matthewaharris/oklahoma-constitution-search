#!/usr/bin/env python3
"""Quick script to collect Title 10 URLs"""

from url_collector import StatuteURLCollector

print("Collecting URLs for Title 10 (Children)...")
print("This is the first actual statute title in Oklahoma\n")

collector = StatuteURLCollector(delay_seconds=10)

# Use Title 10 instead of Title 1
urls = collector.collect_title(10)
collector.save_urls(urls, 'title_10_urls.json')

print(f"\n[SUCCESS] Collected {len(urls)} URLs for Title 10")
print("Saved to: title_10_urls.json")
