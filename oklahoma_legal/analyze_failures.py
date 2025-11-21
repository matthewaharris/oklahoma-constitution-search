#!/usr/bin/env python3
"""
Analyze failed scraping attempts and create retry lists
"""

import json
import glob
from collections import Counter

def analyze_scraping_failures():
    """Analyze the latest scraping results to understand failures"""

    # Find the most recent results file
    result_files = glob.glob('constitution_scrape_results_*.json')

    if not result_files:
        print("No scraping results files found!")
        return

    # Get the most recent file
    latest_file = sorted(result_files)[-1]
    print(f"Analyzing results from: {latest_file}")

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
    except Exception as e:
        print(f"Error reading results file: {e}")
        return

    print("\n" + "="*60)
    print("SCRAPING RESULTS ANALYSIS")
    print("="*60)

    print(f"Total requested: {results['total_requested']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {(results['successful']/results['total_requested']*100):.1f}%")

    # Analyze error types
    if 'errors' in results and results['errors']:
        print(f"\nERROR ANALYSIS:")
        print("-" * 40)

        # Count error types
        error_types = Counter()
        failed_cite_ids = []

        for error in results['errors']:
            cite_id = error['cite_id']
            error_msg = error['error']
            failed_cite_ids.append(cite_id)

            # Categorize errors
            if 'timeout' in error_msg.lower():
                error_types['Timeout'] += 1
            elif 'not found' in error_msg.lower() or '404' in error_msg:
                error_types['Not Found (404)'] += 1
            elif 'connection' in error_msg.lower():
                error_types['Connection Error'] += 1
            elif 'cloudflare' in error_msg.lower() or 'forbidden' in error_msg.lower():
                error_types['Access Blocked'] += 1
            elif 'invalid' in error_msg.lower() or 'parse' in error_msg.lower():
                error_types['Parse Error'] += 1
            else:
                error_types['Other'] += 1

        print("Error breakdown:")
        for error_type, count in error_types.most_common():
            percentage = (count / len(results['errors'])) * 100
            print(f"  {error_type}: {count} ({percentage:.1f}%)")

        # Show sample errors
        print(f"\nSample errors (first 5):")
        for i, error in enumerate(results['errors'][:5]):
            print(f"  {i+1}. CiteID {error['cite_id']}: {error['error'][:80]}...")

        # Save failed cite IDs for retry
        with open('failed_cite_ids.txt', 'w') as f:
            f.write('\n'.join(failed_cite_ids))

        print(f"\n✓ Saved {len(failed_cite_ids)} failed cite IDs to: failed_cite_ids.txt")

        # Analyze successful ones for patterns
        successful_details = []
        for detail in results.get('details', []):
            if detail['success'] and detail['action'] != 'skipped':
                successful_details.append(detail)

        if successful_details:
            print(f"\nSUCCESSFUL SECTIONS ANALYSIS:")
            print("-" * 40)
            print(f"Successfully scraped {len(successful_details)} sections")

            # Show sample successful cite IDs
            sample_successful = [d['cite_id'] for d in successful_details[:10]]
            print(f"Sample successful cite IDs: {', '.join(sample_successful)}")

    return results

def create_retry_script():
    """Create a script to retry only the failed cite IDs"""

    retry_script = '''#!/usr/bin/env python3
"""
Retry failed Oklahoma Constitution sections
"""

from integrated_scraper import IntegratedStatutesScraper
import time

def retry_failed_sections():
    """Retry scraping the failed sections with longer delays"""

    # Load failed cite IDs
    try:
        with open('failed_cite_ids.txt', 'r') as f:
            failed_cite_ids = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("failed_cite_ids.txt not found!")
        print("Run 'python analyze_failures.py' first")
        return

    print(f"Retrying {len(failed_cite_ids)} failed sections...")
    print("Using longer delays to avoid rate limiting")

    # Use longer delay for retry attempts
    scraper = IntegratedStatutesScraper(delay_seconds=3.0)

    print("\\nStarting retry process...")
    print("=" * 50)

    results = scraper.bulk_scrape_statutes(failed_cite_ids, force_update=False)

    print("\\n" + "="*50)
    print("RETRY COMPLETED")
    print("="*50)

    print(f"Retry results:")
    print(f"  Attempted: {results['total_requested']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Still failed: {results['failed']}")
    print(f"  Retry success rate: {(results['successful']/results['total_requested']*100):.1f}%")

    # Save retry results
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"constitution_retry_results_{timestamp}.json"

    import json
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\\nRetry results saved to: {results_file}")

    # Update failed list if there are still failures
    if results['failed'] > 0:
        still_failed = []
        for detail in results['details']:
            if not detail['success']:
                still_failed.append(detail['cite_id'])

        if still_failed:
            with open('still_failed_cite_ids.txt', 'w') as f:
                f.write('\\n'.join(still_failed))
            print(f"✓ Saved {len(still_failed)} still-failed cite IDs to: still_failed_cite_ids.txt")

if __name__ == "__main__":
    retry_failed_sections()
'''

    with open('retry_failed.py', 'w', encoding='utf-8') as f:
        f.write(retry_script)

    print("✓ Created retry script: retry_failed.py")

def main():
    print("Constitution Scraping Failure Analysis")
    print("=" * 40)

    results = analyze_scraping_failures()

    if results and results.get('failed', 0) > 0:
        create_retry_script()

        print(f"\nNEXT STEPS:")
        print("=" * 20)
        print("1. Review the error analysis above")
        print("2. Run 'python retry_failed.py' to retry failed sections")
        print("3. Run 'python show_data.py' to see your current data")

        # Show current database status
        print(f"\nCURRENT DATABASE STATUS:")
        try:
            from supabase_client import StatutesDatabase
            db = StatutesDatabase()
            stats = db.get_database_stats()
            print(f"Database contains:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Could not get database stats: {e}")

if __name__ == "__main__":
    main()
'''