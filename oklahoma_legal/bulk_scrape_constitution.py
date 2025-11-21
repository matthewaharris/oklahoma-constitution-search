#!/usr/bin/env python3
"""
Bulk scraper for Oklahoma Constitution sections
Run this script independently to scrape constitution without using Claude credits
"""

import json
import time
import sys
from datetime import datetime
from integrated_scraper import IntegratedStatutesScraper

def load_constitution_cite_ids():
    """Load cite IDs from various sources"""
    cite_ids = []

    # Try to load from the explorer results
    try:
        with open('oklahoma_constitution_sections.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            cite_ids = [item['cite_id'] for item in data]
            print(f"Loaded {len(cite_ids)} cite IDs from oklahoma_constitution_sections.json")
            return cite_ids
    except FileNotFoundError:
        print("oklahoma_constitution_sections.json not found")

    # Try simple text file
    try:
        with open('constitution_cite_ids.txt', 'r') as f:
            cite_ids = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(cite_ids)} cite IDs from constitution_cite_ids.txt")
            return cite_ids
    except FileNotFoundError:
        print("constitution_cite_ids.txt not found")

    # Manual list of known Oklahoma Constitution cite IDs (if we find them)
    # These would need to be discovered first
    manual_cite_ids = [
        # Add known constitution cite IDs here
        # Example: '123456', '123457', etc.
    ]

    if manual_cite_ids:
        print(f"Using manual list of {len(manual_cite_ids)} cite IDs")
        return manual_cite_ids

    # If no cite IDs found, try a range search
    print("No constitution cite IDs found. Will try range search...")
    return None

def search_constitution_range():
    """Search for constitution sections in likely cite ID ranges"""
    scraper = IntegratedStatutesScraper(delay_seconds=2.0)

    print("Searching for Oklahoma Constitution sections...")
    print("This may take a while as we test different cite ID ranges...")

    found_cite_ids = []

    # Test ranges where constitution sections might be located
    test_ranges = [
        range(1, 50),           # Very low numbers
        range(100, 200),        # Low hundreds
        range(400000, 400050),  # Similar to statute range
        range(450000, 450050),  # Another statute-like range
        range(500000, 500050),  # Higher range
    ]

    for test_range in test_ranges:
        print(f"\nTesting range {test_range.start}-{test_range.stop-1}...")

        for cite_id in test_range:
            try:
                # Test if this cite ID exists and contains constitution content
                result = scraper.scraper.scrape_statute(str(cite_id))

                if result and result.get('content'):
                    # Check if content looks like constitution
                    main_text = result['content'].get('main_text', '').lower()
                    metadata = result.get('metadata', {})
                    section_name = metadata.get('section_name', '').lower()

                    constitution_keywords = [
                        'oklahoma constitution',
                        'article',
                        'preamble',
                        'constitution',
                        'constitutional',
                        'we, the people'
                    ]

                    if any(keyword in main_text or keyword in section_name
                          for keyword in constitution_keywords):
                        found_cite_ids.append(str(cite_id))
                        print(f"  ✓ Found constitution section: {cite_id} - {metadata.get('section_name', 'Unknown')}")

                        # Save immediately in case we get interrupted
                        with open('found_constitution_cite_ids.txt', 'a') as f:
                            f.write(f"{cite_id}\n")

                time.sleep(1)  # Be respectful to the server

            except Exception as e:
                print(f"  Error testing {cite_id}: {e}")
                continue

        # If we found some in this range, we might want to expand the search
        if found_cite_ids:
            print(f"Found {len(found_cite_ids)} constitution sections in range {test_range.start}-{test_range.stop-1}")

            # Test a wider range around the successful range
            expanded_start = max(1, test_range.start - 20)
            expanded_end = test_range.stop + 20

            print(f"Expanding search to {expanded_start}-{expanded_end}...")

            for cite_id in range(expanded_start, expanded_end):
                if cite_id in test_range:
                    continue  # Already tested

                try:
                    result = scraper.scraper.scrape_statute(str(cite_id))

                    if result and result.get('content'):
                        main_text = result['content'].get('main_text', '').lower()
                        metadata = result.get('metadata', {})
                        section_name = metadata.get('section_name', '').lower()

                        if any(keyword in main_text or keyword in section_name
                              for keyword in constitution_keywords):
                            found_cite_ids.append(str(cite_id))
                            print(f"  ✓ Found additional: {cite_id} - {metadata.get('section_name', 'Unknown')}")

                            with open('found_constitution_cite_ids.txt', 'a') as f:
                                f.write(f"{cite_id}\n")

                    time.sleep(1)

                except Exception as e:
                    continue

            break  # Found constitution sections, stop searching other ranges

    return found_cite_ids

def bulk_scrape_constitution(cite_ids, force_update=False):
    """Bulk scrape constitution sections and store in database"""
    if not cite_ids:
        print("No cite IDs to scrape!")
        return

    scraper = IntegratedStatutesScraper(delay_seconds=1.5)

    print(f"\nStarting bulk scrape of {len(cite_ids)} Oklahoma Constitution sections")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)

    results = scraper.bulk_scrape_statutes(cite_ids, force_update=force_update)

    print("\n" + "=" * 60)
    print("BULK SCRAPE COMPLETED")
    print("=" * 60)

    print(f"Total requested: {results['total_requested']}")
    print(f"Successful: {results['successful']}")
    print(f"Skipped (already exists): {results['skipped']}")
    print(f"Failed: {results['failed']}")
    print(f"Total time: {results['elapsed_seconds']:.2f} seconds")
    print(f"Average time per section: {results['average_time_per_statute']:.2f} seconds")

    if results['errors']:
        print(f"\nErrors encountered:")
        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"  {error['cite_id']}: {error['error']}")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"constitution_scrape_results_{timestamp}.json"

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nDetailed results saved to: {results_file}")

    # Show database stats
    stats = scraper.get_scraping_stats()
    print(f"\nDatabase now contains:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

def main():
    print("Oklahoma Constitution Bulk Scraper")
    print("=" * 40)

    # Check command line arguments
    force_update = '--force' in sys.argv
    search_mode = '--search' in sys.argv

    if search_mode:
        print("Search mode: Looking for constitution sections...")
        cite_ids = search_constitution_range()
        if cite_ids:
            print(f"\nFound {len(cite_ids)} constitution sections!")

            # Ask if user wants to proceed with scraping
            response = input("\nProceed with scraping these sections? (y/n): ").lower()
            if response == 'y':
                bulk_scrape_constitution(cite_ids, force_update)
        else:
            print("No constitution sections found in search.")
    else:
        # Normal mode: try to load existing cite IDs
        cite_ids = load_constitution_cite_ids()

        if not cite_ids:
            print("\nNo constitution cite IDs found!")
            print("Options:")
            print("1. Run the explorer first: python explore_constitution.py")
            print("2. Use search mode: python bulk_scrape_constitution.py --search")
            print("3. Manually add cite IDs to constitution_cite_ids.txt")
            return

        print(f"\nFound {len(cite_ids)} constitution sections to scrape")

        if force_update:
            print("Force update mode: Will re-scrape existing sections")

        response = input(f"\nProceed with scraping {len(cite_ids)} sections? (y/n): ").lower()

        if response == 'y':
            bulk_scrape_constitution(cite_ids, force_update)
        else:
            print("Scraping cancelled.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure your database connection is configured correctly.")