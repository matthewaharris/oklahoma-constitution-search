#!/usr/bin/env python3
"""
Simple runner script for Oklahoma Constitution scraping
Execute this to automatically discover and scrape constitution sections
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and show progress"""
    print(f"\n{description}")
    print("=" * 50)

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout)
            if result.stderr:
                print("Warnings/Info:")
                print(result.stderr)
            return True
        else:
            print(f"Error running command: {command}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except Exception as e:
        print(f"Exception running command: {e}")
        return False

def main():
    print("Oklahoma Constitution Scraper - Automated Runner")
    print("=" * 60)
    print("This script will:")
    print("1. Explore OSCN to find Oklahoma Constitution structure")
    print("2. Automatically scrape all found constitution sections")
    print("3. Store everything in your Supabase database")
    print()

    response = input("Continue? (y/n): ").lower()
    if response != 'y':
        print("Cancelled.")
        return

    # Step 1: Explore constitution structure
    print("\nSTEP 1: Discovering Oklahoma Constitution sections on OSCN...")
    success = run_command("python explore_constitution.py", "Exploring constitution structure")

    if not success:
        print("Failed to explore constitution structure.")
        return

    # Check if we found constitution sections
    if os.path.exists('oklahoma_constitution_sections.json'):
        print("✓ Found constitution sections!")
    elif os.path.exists('constitution_cite_ids.txt'):
        print("✓ Found constitution cite IDs!")
    else:
        print("No constitution sections found in exploration.")
        print("Trying search mode...")

        # Step 2: Search mode if exploration didn't work
        success = run_command("python bulk_scrape_constitution.py --search",
                             "Searching for constitution sections")

        if not success:
            print("Search also failed. You may need to manually find constitution cite IDs.")
            return

    # Step 3: Bulk scrape
    print("\nSTEP 2: Starting bulk scrape of constitution sections...")
    success = run_command("python bulk_scrape_constitution.py",
                          "Bulk scraping constitution sections")

    if success:
        print("\n" + "=" * 60)
        print("CONSTITUTION SCRAPING COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        # Show final database stats
        print("\nFinal step: Checking database contents...")
        run_command("python show_data.py", "Showing database contents")

        print("\nFiles created:")
        files_to_check = [
            'oklahoma_constitution_sections.json',
            'constitution_cite_ids.txt',
            'constitution_scrape_results_*.json'
        ]

        for filename in files_to_check:
            if '*' in filename:
                import glob
                matches = glob.glob(filename)
                for match in matches:
                    print(f"  ✓ {match}")
            elif os.path.exists(filename):
                print(f"  ✓ {filename}")

    else:
        print("Bulk scraping failed. Check the error messages above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")