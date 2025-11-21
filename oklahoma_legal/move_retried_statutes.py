"""
Move the 25 retried statute files from statute_html to appropriate title directories.
We'll need to parse each HTML file to determine which title it belongs to.
"""

import json
import shutil
from pathlib import Path
from bs4 import BeautifulSoup

SOURCE_DIR = Path("statute_html")
TARGET_DIR = Path("html_files/statutes")

def extract_title_from_html(html_path):
    """Extract the title number from an HTML file"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        # Look for citation patterns like "11 O.S. § 1-101" or "Title 11"
        text = soup.get_text()

        # Try to find "Title X" pattern
        import re
        title_match = re.search(r'Title\s+(\d+)', text, re.IGNORECASE)
        if title_match:
            return int(title_match.group(1))

        # Try to find "X O.S." pattern
        os_match = re.search(r'(\d+)\s+O\.?S\.?', text)
        if os_match:
            return int(os_match.group(1))

        # Try citation format
        cite_match = re.search(r'§\s*(\d+)-', text)
        if cite_match:
            return int(cite_match.group(1))

        return None

    except Exception as e:
        print(f"  Error parsing {html_path.name}: {e}")
        return None

def main():
    print("=" * 70)
    print("MOVING RETRIED STATUTE FILES TO TITLE DIRECTORIES")
    print("=" * 70)

    # Get all HTML files from source directory
    html_files = list(SOURCE_DIR.glob("*.html"))
    print(f"\nFound {len(html_files)} files to move\n")

    moved_count = 0
    failed_count = 0

    for html_file in html_files:
        print(f"Processing {html_file.name}...")

        # Extract title number
        title_num = extract_title_from_html(html_file)

        if title_num:
            # Create target directory if needed
            target_title_dir = TARGET_DIR / f"title_{title_num}"
            target_title_dir.mkdir(parents=True, exist_ok=True)

            # Move file
            target_file = target_title_dir / html_file.name
            shutil.move(str(html_file), str(target_file))

            print(f"  Moved to title_{title_num}/")
            moved_count += 1
        else:
            print(f"  WARNING: Could not determine title number")
            failed_count += 1

        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Successfully moved: {moved_count}")
    print(f"Failed to move: {failed_count}")

    # Verify source directory is empty
    remaining = list(SOURCE_DIR.glob("*.html"))
    if remaining:
        print(f"\nRemaining files in {SOURCE_DIR}: {len(remaining)}")
    else:
        print(f"\n{SOURCE_DIR} is now empty")

if __name__ == "__main__":
    main()
