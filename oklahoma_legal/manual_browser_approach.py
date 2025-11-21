#!/usr/bin/env python3
"""
Manual browser approach for getting Oklahoma Constitution data
This approach helps when Cloudflare is blocking automated requests
"""

import json
import os
from pathlib import Path

def manual_html_parser():
    """Parse manually saved HTML files"""
    print("Manual HTML Parser for Oklahoma Constitution")
    print("=" * 50)
    print()
    print("If Cloudflare is blocking automated access, you can:")
    print("1. Manually visit: https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKCN&level=1")
    print("2. Right-click → 'Save as' → Save as 'constitution_manual.html'")
    print("3. Run this script to extract the cite IDs")
    print()

    # Look for manually saved HTML files
    possible_files = [
        'constitution_manual.html',
        'constitution_root_page.html',
        'constitution.html',
        'oscn_constitution.html'
    ]

    html_file = None
    for filename in possible_files:
        if os.path.exists(filename):
            html_file = filename
            break

    if not html_file:
        print("❌ No HTML file found!")
        print("\nTo manually save the constitution page:")
        print("1. Open: https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKCN&level=1")
        print("2. Right-click on the page → 'Save as'")
        print("3. Save as 'constitution_manual.html' in this directory")
        print("4. Run this script again")
        return

    print(f"✓ Found HTML file: {html_file}")

    # Parse the HTML file
    try:
        from bs4 import BeautifulSoup
        import re

        # Try multiple encodings to handle different file saves
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        html_content = None

        for encoding in encodings:
            try:
                with open(html_file, 'r', encoding=encoding) as f:
                    html_content = f.read()
                print(f"✓ Loaded HTML file with {encoding} encoding ({len(html_content)} characters)")
                break
            except UnicodeDecodeError:
                continue

        if html_content is None:
            print("❌ Could not decode the HTML file with any common encoding")
            return

        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract constitution sections
        links = soup.find_all('a', href=True)
        print(f"Found {len(links)} total links")

        constitution_sections = []

        for link in links:
            href = link['href']
            text = link.get_text().strip()

            if 'DeliverDocument.asp?CiteID=' in href:
                cite_id_match = re.search(r'CiteID=(\d+)', href)
                if cite_id_match:
                    cite_id = cite_id_match.group(1)

                    constitution_sections.append({
                        'cite_id': cite_id,
                        'text': text,
                        'href': href,
                        'full_url': f"https://www.oscn.net{href}" if not href.startswith('http') else href
                    })

        if constitution_sections:
            print(f"✓ Found {len(constitution_sections)} constitution sections!")

            # Show preview
            print("\nSections found:")
            for i, section in enumerate(constitution_sections[:10]):
                print(f"  {i+1:2d}. CiteID {section['cite_id']:>6}: {section['text'][:60]}...")

            if len(constitution_sections) > 10:
                print(f"  ... and {len(constitution_sections) - 10} more")

            # Save results
            with open('oklahoma_constitution_sections.json', 'w', encoding='utf-8') as f:
                json.dump(constitution_sections, f, indent=2, ensure_ascii=False)

            cite_ids = [section['cite_id'] for section in constitution_sections]
            with open('constitution_cite_ids.txt', 'w') as f:
                f.write('\n'.join(cite_ids))

            print(f"\n✓ Saved to: oklahoma_constitution_sections.json")
            print(f"✓ Saved cite IDs to: constitution_cite_ids.txt")

            print(f"\nNext step: Run 'python bulk_scrape_constitution.py' to scrape these sections")

        else:
            print("❌ No constitution sections found in the HTML file")
            print("The file might not contain the expected structure.")

    except Exception as e:
        print(f"❌ Error parsing HTML file: {e}")

def create_selenium_script():
    """Create a Selenium script for browser automation"""
    selenium_script = '''#!/usr/bin/env python3
"""
Selenium-based Oklahoma Constitution scraper
Install: pip install selenium
Download ChromeDriver: https://chromedriver.chromium.org/
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import re

def scrape_with_selenium():
    # Set up Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment to run headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print("Loading Oklahoma Constitution page...")
        driver.get("https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKCN&level=1")

        # Wait for page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        print("Page loaded, waiting for any Cloudflare checks...")
        time.sleep(10)  # Wait for any Cloudflare checks to complete

        # Get page source
        html_content = driver.page_source

        # Save the page
        with open('constitution_selenium.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        print("✓ Page saved to: constitution_selenium.html")

        # Parse links
        links = driver.find_elements(By.TAG_NAME, "a")
        constitution_sections = []

        for link in links:
            try:
                href = link.get_attribute('href')
                text = link.text.strip()

                if href and 'DeliverDocument.asp?CiteID=' in href:
                    cite_id_match = re.search(r'CiteID=(\d+)', href)
                    if cite_id_match:
                        cite_id = cite_id_match.group(1)
                        constitution_sections.append({
                            'cite_id': cite_id,
                            'text': text,
                            'href': href
                        })
            except:
                continue

        print(f"Found {len(constitution_sections)} constitution sections")

        # Save results
        with open('constitution_sections_selenium.json', 'w', encoding='utf-8') as f:
            json.dump(constitution_sections, f, indent=2, ensure_ascii=False)

        return constitution_sections

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_with_selenium()
'''

    with open('selenium_constitution_scraper.py', 'w', encoding='utf-8') as f:
        f.write(selenium_script)

    print("✓ Created Selenium script: selenium_constitution_scraper.py")
    print("\nTo use Selenium approach:")
    print("1. pip install selenium")
    print("2. Download ChromeDriver from: https://chromedriver.chromium.org/")
    print("3. python selenium_constitution_scraper.py")

def main():
    print("Choose an approach to bypass Cloudflare:")
    print("1. Try the enhanced scraper with better headers")
    print("2. Parse manually saved HTML file")
    print("3. Create Selenium browser automation script")
    print("4. Exit")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == '1':
        print("Run: python cloudflare_bypass_scraper.py")
    elif choice == '2':
        manual_html_parser()
    elif choice == '3':
        create_selenium_script()
    elif choice == '4':
        print("Goodbye!")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()