#!/usr/bin/env python3
"""Debug script to examine OSCN HTML structure"""

import requests
from bs4 import BeautifulSoup
import time

# Fetch Title 1 index page
url = "https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKST1&level=1"
print(f"Fetching: {url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Educational Legal Research Tool - Contact: mharris26@gmail.com)'
}

response = requests.get(url, headers=headers, timeout=30)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)} characters\n")

# Save the HTML for inspection
with open('oscn_title1_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("Saved HTML to: oscn_title1_page.html\n")

# Parse and look for links
soup = BeautifulSoup(response.text, 'html.parser')

# Find all links
all_links = soup.find_all('a', href=True)
print(f"Total links found: {len(all_links)}\n")

# Look for different types of links
deliverdoc_links = [link for link in all_links if 'DeliverDocument' in link.get('href', '')]
print(f"DeliverDocument links: {len(deliverdoc_links)}")

if deliverdoc_links:
    print("\nFirst 5 DeliverDocument links:")
    for link in deliverdoc_links[:5]:
        print(f"  Text: {link.get_text(strip=True)[:50]}")
        print(f"  Href: {link['href'][:100]}")
        print()
else:
    print("\nNo DeliverDocument links found!")
    print("\nAll link types found:")
    href_patterns = {}
    for link in all_links[:20]:
        href = link.get('href', '')
        if 'asp' in href.lower():
            pattern = href.split('?')[0] if '?' in href else href
            href_patterns[pattern] = href_patterns.get(pattern, 0) + 1

    for pattern, count in sorted(href_patterns.items()):
        print(f"  {pattern}: {count} links")

    print("\nFirst 10 links:")
    for link in all_links[:10]:
        print(f"  Text: {link.get_text(strip=True)[:50]}")
        print(f"  Href: {link['href'][:100]}")
        print()
