#!/usr/bin/env python3
"""Stop the download process cleanly"""
import psutil
import sys

killed = False
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = proc.info['cmdline']
        if cmdline and 'monitor_and_download.py' in ' '.join(cmdline):
            print(f"Stopping download process (PID {proc.info['pid']})...")
            proc.terminate()
            proc.wait(timeout=5)
            print("Download process stopped successfully")
            killed = True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
        pass

if not killed:
    print("No download process found running")
