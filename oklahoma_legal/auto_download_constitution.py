#!/usr/bin/env python3
"""
Automated browser-based download of Oklahoma Constitution sections
Using Selenium to bypass Cloudflare Turnstile
"""

import json
import time
import os
from pathlib import Path

def create_selenium_downloader():
    """Create selenium script for automated downloads"""

    selenium_script = '''#!/usr/bin/env python3
"""
Selenium-based automated downloader for Oklahoma Constitution
Requires: pip install selenium
Download ChromeDriver: https://chromedriver.chromium.org/
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import json
import os
from pathlib import Path

def setup_driver():
    """Setup Chrome driver with human-like options"""
    chrome_options = Options()

    # Make browser appear more human-like
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Optional: run headless (uncomment if you want to see the browser)
    # chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)

    # Execute script to remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def download_constitution_sections():
    """Download all constitution sections automatically"""

    # Load URLs to download
    try:
        with open('constitution_urls_to_download.json', 'r', encoding='utf-8') as f:
            urls_data = json.load(f)
    except FileNotFoundError:
        print("❌ constitution_urls_to_download.json not found!")
        print("Run 'python manual_constitution_workflow.py' first and choose option 1")
        return

    # Create output folder
    output_folder = Path('constitution_html')
    output_folder.mkdir(exist_ok=True)

    print(f"Starting automated download of {len(urls_data)} constitution sections...")
    print("This will take a while - browser will open and visit each URL")
    print("Press Ctrl+C to stop at any time")

    driver = setup_driver()

    try:
        successful_downloads = 0
        failed_downloads = 0

        for i, url_info in enumerate(urls_data, 1):
            cite_id = url_info['cite_id']
            url = url_info['url']
            filename = output_folder / url_info['filename']

            # Skip if already downloaded
            if filename.exists():
                print(f"{i:3d}/{len(urls_data)} Skipping {cite_id} (already exists)")
                continue

            print(f"{i:3d}/{len(urls_data)} Downloading CiteID {cite_id}...")

            try:
                # Navigate to the page
                driver.get(url)

                # Wait for page to load and handle any Turnstile challenges
                print(f"    Waiting for page to load...")

                # Wait for body element to be present
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Additional wait for Turnstile/Cloudflare
                time.sleep(5)

                # Check if we got a valid page (not Turnstile challenge)
                page_source = driver.page_source

                if ('turnstile' in page_source.lower() or
                    'cloudflare' in page_source.lower() or
                    'just a moment' in page_source.lower()):
                    print(f"    ⚠️ Cloudflare challenge detected, waiting longer...")
                    time.sleep(15)  # Wait longer for challenge to resolve
                    page_source = driver.page_source

                # Save the page
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(page_source)

                print(f"    ✓ Saved {filename}")
                successful_downloads += 1

                # Human-like delay between downloads
                time.sleep(2 + (i % 3))  # 2-4 second delay

            except TimeoutException:
                print(f"    ❌ Timeout loading {cite_id}")
                failed_downloads += 1
            except Exception as e:
                print(f"    ❌ Error downloading {cite_id}: {e}")
                failed_downloads += 1

            # Progress update every 20 downloads
            if i % 20 == 0:
                print(f"\\nProgress: {i}/{len(urls_data)} - Success: {successful_downloads}, Failed: {failed_downloads}\\n")

        print(f"\\nDownload completed!")
        print(f"Successfully downloaded: {successful_downloads}")
        print(f"Failed: {failed_downloads}")
        print(f"Total files in folder: {len(list(output_folder.glob('*.html')))}")

    except KeyboardInterrupt:
        print(f"\\nDownload interrupted by user")
        print(f"Downloaded so far: {successful_downloads}")

    finally:
        driver.quit()

if __name__ == "__main__":
    try:
        download_constitution_sections()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have:")
        print("1. Installed selenium: pip install selenium")
        print("2. Downloaded ChromeDriver and added it to PATH")
'''

    with open('auto_download_constitution.py', 'w', encoding='utf-8') as f:
        f.write(selenium_script)

    print("✓ Created automated download script: auto_download_constitution.py")

def create_cleanup_script():
    """Create a script to clean up NULL/Turnstile records"""

    cleanup_script = '''#!/usr/bin/env python3
"""
Clean up NULL and Turnstile records from the database
"""

from supabase_client import StatutesDatabase

def cleanup_bad_records():
    """Remove or identify records with NULL data or Turnstile pages"""

    db = StatutesDatabase()

    print("Analyzing database for bad records...")

    # Find records with "OSCN Turnstile" in page_title
    turnstile_query = db.client.table('statutes').select('cite_id, page_title, main_text').execute()

    turnstile_records = []
    null_records = []

    for record in turnstile_query.data:
        page_title = record.get('page_title', '')
        main_text = record.get('main_text', '')
        cite_id = record['cite_id']

        if 'turnstile' in page_title.lower():
            turnstile_records.append(cite_id)
        elif not main_text or main_text.strip() == '':
            null_records.append(cite_id)

    print(f"Found {len(turnstile_records)} Turnstile records")
    print(f"Found {len(null_records)} NULL/empty records")

    # Save the bad cite IDs for manual processing
    bad_cite_ids = list(set(turnstile_records + null_records))

    with open('bad_cite_ids_to_reprocess.txt', 'w') as f:
        f.write('\\n'.join(bad_cite_ids))

    print(f"\\nSaved {len(bad_cite_ids)} bad cite IDs to: bad_cite_ids_to_reprocess.txt")
    print("\\nThese are the cite IDs you should focus on for manual download")

    return bad_cite_ids

if __name__ == "__main__":
    cleanup_bad_records()
'''

    with open('cleanup_bad_records.py', 'w', encoding='utf-8') as f:
        f.write(cleanup_script)

    print("✓ Created cleanup script: cleanup_bad_records.py")

def main():
    print("Constitution Manual Download Setup")
    print("=" * 40)

    create_selenium_downloader()
    create_cleanup_script()

    print("\nSetup complete! You now have:")
    print("1. manual_constitution_workflow.py - Main workflow script")
    print("2. auto_download_constitution.py - Automated Selenium downloader")
    print("3. cleanup_bad_records.py - Find bad database records")

    print("\nRecommended workflow:")
    print("1. Run: python cleanup_bad_records.py")
    print("2. Run: python manual_constitution_workflow.py (option 1)")
    print("3. Either:")
    print("   - Manual: Download HTML files following instructions")
    print("   - Auto: python auto_download_constitution.py (requires selenium)")
    print("4. Run: python manual_constitution_workflow.py (option 2)")

if __name__ == "__main__":
    main()