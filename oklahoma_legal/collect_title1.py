#!/usr/bin/env python3
"""Quick script to collect Title 1 URLs"""

from url_collector import StatuteURLCollector

print("Collecting URLs for Title 1...")
collector = StatuteURLCollector(delay_seconds=10)
urls = collector.collect_title(1)
collector.save_urls(urls, 'title_1_urls.json')
print(f"\n[SUCCESS] Collected {len(urls)} URLs for Title 1")
print("Saved to: title_1_urls.json")
