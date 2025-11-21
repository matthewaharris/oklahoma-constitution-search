#!/usr/bin/env python3
"""
Process the downloaded statute HTML files and upload to Pinecone
Non-interactive version - automatically processes all files
"""

import sys
from pathlib import Path

# Import HTML processor components
from html_processor import StatuteHTMLProcessor

print("Processing Downloaded Oklahoma Statutes")
print("=" * 60)
print("This will process all HTML files in statute_html/title_10/")
print("NON-INTERACTIVE MODE - No confirmation needed")
print("=" * 60)
print()

# Create processor
processor = StatuteHTMLProcessor()

# Process all files in title_10 directory
print("Starting HTML processing...")
print()

try:
    # Modified version without interactive prompt
    # Count files first
    html_files = []
    title_dir = Path('statute_html/title_10')
    if title_dir.exists():
        html_files = list(title_dir.glob('*.html'))

    total_files = len(html_files)
    print(f"Found {total_files} HTML files to process")
    print(f"Already processed: {len(processor.processed)}")
    remaining = total_files - len(processor.processed)
    print(f"Will process: {remaining} files")
    print()

    # Process without confirmation
    processor.process_all_html_files(start_title=10, end_title=10)

    print("\n" + "=" * 60)
    print("[SUCCESS] Processing complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test search functionality")
    print("2. Update web app to search statutes")
    print("3. Deploy updated app")

except KeyboardInterrupt:
    print("\n\nProcessing interrupted by user")
    print("Progress has been saved. You can resume with:")
    print("  python process_downloaded_statutes.py")

except Exception as e:
    print(f"\n[ERROR] Processing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
