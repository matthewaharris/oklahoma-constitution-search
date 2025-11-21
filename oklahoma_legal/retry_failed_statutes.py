"""
Retry downloading failed statute documents from OSCN.
Reads failed entries from statute_download_progress.json and retries them.
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime

# Configuration
PROGRESS_FILE = "statute_download_progress.json"
HTML_DIR = Path("statute_html")
TIMEOUT = 60  # Increased from 30 to 60 seconds
DELAY_BETWEEN_REQUESTS = 2  # 2 seconds between requests

def load_progress():
    """Load the progress file"""
    with open(PROGRESS_FILE, 'r') as f:
        return json.load(f)

def save_progress(data):
    """Save updated progress"""
    data['last_updated'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def download_statute(cite_id, url, max_retries=3):
    """
    Download a single statute with retries

    Args:
        cite_id: The CiteID for the statute
        url: The URL to download from
        max_retries: Maximum number of retry attempts

    Returns:
        tuple: (success: bool, html_content: str or None, error_msg: str or None)
    """
    for attempt in range(max_retries):
        try:
            print(f"  Attempt {attempt + 1}/{max_retries}...", end=" ")

            response = requests.get(
                url,
                timeout=TIMEOUT,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )

            if response.status_code == 200:
                print("SUCCESS")
                return True, response.text, None
            else:
                print(f"FAILED: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff

        except requests.exceptions.Timeout:
            print(f"TIMEOUT")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except Exception as e:
            print(f"ERROR: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return False, None, f"Failed after {max_retries} attempts"

def main():
    """Main retry function"""
    print("=" * 70)
    print("RETRY FAILED STATUTE DOWNLOADS")
    print("=" * 70)

    # Ensure HTML directory exists
    HTML_DIR.mkdir(exist_ok=True)

    # Load progress
    print("\nLoading progress file...")
    progress = load_progress()

    failed_list = progress.get('failed', [])
    print(f"Found {len(failed_list)} failed downloads to retry\n")

    if not failed_list:
        print("No failed downloads to retry!")
        return

    # Track results
    newly_successful = []
    still_failed = []

    # Retry each failed download
    for i, failed_item in enumerate(failed_list, 1):
        cite_id = failed_item['cite_id']
        url = failed_item['url']

        print(f"[{i}/{len(failed_list)}] Retrying CiteID {cite_id}...")

        success, html_content, error_msg = download_statute(cite_id, url)

        if success:
            # Save the HTML file
            filename = HTML_DIR / f"{cite_id}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Add to successful downloads
            newly_successful.append({
                'cite_id': cite_id,
                'url': url,
                'filename': str(filename),
                'timestamp': datetime.now().isoformat()
            })

            print(f"  SAVED to {filename}\n")

        else:
            # Keep in failed list
            still_failed.append({
                'cite_id': cite_id,
                'url': url,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            print(f"  STILL FAILED: {error_msg}\n")

        # Delay between requests
        if i < len(failed_list):
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Update progress file
    print("\n" + "=" * 70)
    print("UPDATING PROGRESS FILE")
    print("=" * 70)

    # Move newly successful items from failed to downloaded
    progress['downloaded'].extend(newly_successful)
    progress['failed'] = still_failed

    save_progress(progress)

    # Print summary
    print(f"\n{'=' * 70}")
    print("RETRY SUMMARY")
    print("=" * 70)
    print(f"Newly successful: {len(newly_successful)}")
    print(f"Still failed: {len(still_failed)}")
    print(f"\nTotal downloaded: {len(progress['downloaded'])}")
    print(f"Total failed: {len(progress['failed'])}")
    print(f"Success rate: {len(progress['downloaded']) / (len(progress['downloaded']) + len(progress['failed'])) * 100:.2f}%")

    if still_failed:
        print(f"\nStill failing CiteIDs:")
        for item in still_failed:
            print(f"  - {item['cite_id']}: {item['error']}")

    print("\nDone!")

if __name__ == "__main__":
    main()
