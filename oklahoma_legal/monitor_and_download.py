#!/usr/bin/env python3
"""
Monitor URL collection and automatically start downloads when complete
"""

import time
import os
import json
import subprocess
import sys

def check_url_collection_complete():
    """Check if URL collection is complete"""

    # Check if the JSON file exists and has data
    if not os.path.exists('oklahoma_statute_urls.json'):
        return False

    try:
        with open('oklahoma_statute_urls.json', 'r') as f:
            data = json.load(f)

        total_urls = data.get('total_urls', 0)

        # Check if we have a significant number of URLs (expecting ~17,000+)
        if total_urls > 15000:
            return True

    except Exception as e:
        print(f"Error checking URL file: {e}")
        return False

    return False

def wait_for_url_collection():
    """Wait for URL collection to complete"""
    print("Monitoring URL collection progress...")
    print("Checking every 30 seconds...")
    print()

    check_count = 0
    while True:
        check_count += 1

        # Check log file for progress
        if os.path.exists('statute_url_collection.log'):
            with open('statute_url_collection.log', 'r') as f:
                lines = f.readlines()

            # Find last progress line
            for line in reversed(lines):
                if 'Progress:' in line:
                    print(f"[{time.strftime('%H:%M:%S')}] {line.strip()}")
                    break
                elif 'SUCCESS' in line and 'Collected' in line:
                    print(f"[{time.strftime('%H:%M:%S')}] URL collection complete!")
                    return True

        # Check if complete
        if check_url_collection_complete():
            print(f"\n[{time.strftime('%H:%M:%S')}] URL collection complete - JSON file ready!")
            return True

        # Wait before next check
        time.sleep(30)

def start_downloads():
    """Start HTML downloads"""
    print("\n" + "="*60)
    print("STARTING HTML DOWNLOADS")
    print("="*60)
    print()

    print("Download sequence:")
    print("1. Constitution HTML files (491 files, ~16 minutes)")
    print("2. Statute HTML files (~49,603 files, ~27.5 hours)")
    print()

    # Import the downloader directly instead of calling subprocess
    sys.path.insert(0, os.path.dirname(__file__))
    from html_downloader import HTMLDownloader

    downloader = HTMLDownloader(delay_seconds=2)

    # Start with Constitution
    print("Starting Constitution download...")
    downloader.download_constitution()

    print("\nConstitution download complete!")
    print("\nStarting Statute download...")

    # Reset downloader for statutes
    downloader = HTMLDownloader(delay_seconds=2)
    downloader.download_statutes()

    print("\nAll downloads complete!")

def main():
    """Main entry point"""
    print("Oklahoma Legal Database - Automated Download Monitor")
    print("="*60)
    print()

    # Check if URL collection is already complete
    if check_url_collection_complete():
        print("URL collection already complete!")
        print("Starting downloads automatically...")
        time.sleep(5)
        start_downloads()
    else:
        # Wait for URL collection
        if wait_for_url_collection():
            print("\nWaiting 10 seconds before starting downloads...")
            time.sleep(10)
            start_downloads()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMonitoring interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
