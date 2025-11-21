#!/usr/bin/env python3
"""
Monitor download and notify when complete
"""

import time
import os
from pathlib import Path
from datetime import datetime
import json

def check_if_complete():
    """Check if download is complete"""
    html_dir = Path('statute_html/title_10')
    if not html_dir.exists():
        return False, 0

    html_files = list(html_dir.glob('*.html'))
    total_downloaded = len(html_files)

    # Load expected count
    try:
        with open('title_10_urls.json', 'r') as f:
            data = json.load(f)
            total_expected = len(data.get('urls', []))
    except:
        total_expected = 1345

    return total_downloaded >= total_expected, total_downloaded

def send_notification():
    """Send completion notification"""
    # Try Windows toast notification
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            "Download Complete!",
            "Title 10 Oklahoma Statutes download finished.\n1,345 statutes ready to process.",
            icon_path=None,
            duration=20,
            threaded=False
        )
    except ImportError:
        # Fallback: System beep and console message
        print("\a" * 3)  # System beep
        print("\n" + "=" * 60)
        print("🎉 DOWNLOAD COMPLETE! 🎉")
        print("=" * 60)
        print("Title 10 Oklahoma Statutes")
        print("All 1,345 statutes have been downloaded")
        print(f"Completed at: {datetime.now().strftime('%I:%M %p')}")
        print("=" * 60)

def write_completion_file(total_downloaded):
    """Write completion status file"""
    with open('DOWNLOAD_COMPLETE.txt', 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("TITLE 10 DOWNLOAD COMPLETE\n")
        f.write("=" * 60 + "\n")
        f.write(f"Completed at: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}\n")
        f.write(f"Total downloaded: {total_downloaded:,} statutes\n")
        f.write(f"Output directory: statute_html/title_10/\n")
        f.write("\n")
        f.write("Next steps:\n")
        f.write("1. python html_processor.py (option 4) - Create Pinecone index\n")
        f.write("2. python html_processor.py (option 1) - Process HTML files\n")
        f.write("3. Test search functionality\n")
        f.write("4. Deploy updated app\n")
        f.write("\n")
        f.write("=" * 60 + "\n")

def main():
    """Monitor and notify"""
    print("Download Completion Monitor")
    print("=" * 60)
    print("Monitoring Title 10 download...")
    print("Will check every 5 minutes")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)
    print()

    check_interval = 300  # 5 minutes

    while True:
        try:
            is_complete, total = check_if_complete()

            if is_complete:
                print(f"\n[{datetime.now().strftime('%I:%M %p')}] Download complete!")
                print(f"Total downloaded: {total:,} statutes")

                # Send notification
                send_notification()

                # Write completion file
                write_completion_file(total)

                # Show final stats
                print("\nFinal Statistics:")
                print(f"  Total files: {total:,}")
                print(f"  Location: statute_html/title_10/")
                print(f"  Completion file: DOWNLOAD_COMPLETE.txt")

                # Check log file for errors
                if os.path.exists('download_title10_full.log'):
                    with open('download_title10_full.log', 'r') as f:
                        log_content = f.read()
                        error_count = log_content.count('[ERROR]')
                        print(f"  Errors encountered: {error_count}")

                print("\nNext: Run html_processor.py to upload to Pinecone")
                break
            else:
                # Show progress
                percent = (total / 1345) * 100
                remaining = 1345 - total
                time_remaining = (remaining * 10) / 60  # minutes

                print(f"[{datetime.now().strftime('%I:%M %p')}] Progress: {total:,}/1,345 ({percent:.1f}%) - Est. {time_remaining:.0f} min remaining")

                # Wait before next check
                time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            print("Download is still running in background")
            print("Run this script again to resume monitoring")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    main()
