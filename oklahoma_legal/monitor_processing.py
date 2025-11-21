#!/usr/bin/env python3
"""
Monitor statute processing progress (Windows-compatible)
"""

import time
import os
from pathlib import Path
from datetime import datetime

def monitor_progress():
    """Monitor and display processing progress"""

    log_file = Path('processing.log')
    progress_file = Path('processing_progress.json')

    print("Oklahoma Statutes Processing Monitor")
    print("=" * 60)
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)
    print()

    last_position = 0
    last_progress = 0

    while True:
        try:
            # Check if log file exists
            if log_file.exists():
                # Get file size
                current_size = log_file.stat().st_size

                if current_size > last_position:
                    # Read new content
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_position)
                        new_content = f.read()
                        last_position = current_size

                        # Show last few lines
                        lines = new_content.strip().split('\n')
                        for line in lines[-10:]:
                            if line.strip():
                                print(line)

                # Check progress file
                if progress_file.exists():
                    import json
                    try:
                        with open(progress_file, 'r') as f:
                            progress = json.load(f)
                            current_count = progress.get('count', 0)

                            if current_count != last_progress:
                                last_progress = current_count
                                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Progress: {current_count} statutes processed")
                                print("=" * 60)
                    except:
                        pass

                # Check if process is still running
                if 'Processing Complete' in new_content or 'SUCCESS' in new_content:
                    print("\n" + "=" * 60)
                    print("PROCESSING COMPLETE!")
                    print("=" * 60)
                    break

            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for processing to start...")

            # Wait before next check
            time.sleep(10)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped")
            print("Processing is still running in background")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_progress()
