#!/usr/bin/env python3
"""
Batch Case Law Scraper
Scrapes all discovered cases and stores them in Supabase
"""

import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Set

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import from same directory
from scrapers.case_law_scraper import CaseLawScraper

class BatchCaseScraper:
    """Batch scrape all discovered cases"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.scraper = CaseLawScraper(supabase_url, supabase_key)
        self.progress_file = "scraping_progress.json"
        self.scraped_cite_ids: Set[str] = set()
        self.failed_cite_ids: List[Dict] = []
        self.load_progress()

    def load_progress(self):
        """Load progress from previous run if exists"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.scraped_cite_ids = set(data.get('scraped', []))
                    self.failed_cite_ids = data.get('failed', [])
                    print(f"[RESUME] Loaded progress: {len(self.scraped_cite_ids)} already scraped")
            except Exception as e:
                print(f"[WARNING] Could not load progress: {e}")

    def save_progress(self):
        """Save current progress"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump({
                    'scraped': list(self.scraped_cite_ids),
                    'failed': self.failed_cite_ids,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Could not save progress: {e}")

    def scrape_all_cases(self, discovered_cases_file: str = "discovered_cases.json"):
        """
        Scrape all cases from discovery file

        Args:
            discovered_cases_file: Path to discovered_cases.json
        """
        # Load discovered cases
        print("="*60)
        print("Oklahoma Case Law Batch Scraper")
        print("="*60)

        with open(discovered_cases_file, 'r') as f:
            discovered_data = json.load(f)

        cases_by_court = discovered_data['cases_by_court']

        # Count total cases
        total_cases = sum(len(cite_ids) for cite_ids in cases_by_court.values())
        already_scraped = len(self.scraped_cite_ids)
        remaining = total_cases - already_scraped

        print(f"\nTotal cases to scrape: {total_cases:,}")
        print(f"Already scraped: {already_scraped:,}")
        print(f"Remaining: {remaining:,}")
        print(f"Estimated time: {remaining * 2 / 60:.0f}-{remaining * 3 / 60:.0f} minutes")
        print("="*60)

        # Scrape each court
        for court_name, cite_ids in cases_by_court.items():
            self.scrape_court_cases(court_name, cite_ids)

        # Final summary
        self.print_summary()

    def scrape_court_cases(self, court_name: str, cite_ids: List[str]):
        """Scrape all cases for a specific court"""
        print(f"\n{'='*60}")
        print(f"Scraping: {court_name}")
        print(f"{'='*60}\n")

        # Map court names to types
        court_type_map = {
            'supreme_court': ('supreme_court', 'STOKCSSC'),
            'criminal_appeals': ('criminal_appeals', 'STOKCSCR'),
            'civil_appeals': ('civil_appeals', 'STOKCSCV')
        }

        court_type, court_db = court_type_map[court_name]

        # Filter out already scraped cases
        remaining_cite_ids = [cid for cid in cite_ids if cid not in self.scraped_cite_ids]

        if not remaining_cite_ids:
            print(f"[SKIP] All {len(cite_ids)} cases already scraped\n")
            return

        print(f"Cases to scrape: {len(remaining_cite_ids)}/{len(cite_ids)}")

        batch = []
        batch_size = 10  # Store in batches

        for i, cite_id in enumerate(remaining_cite_ids):
            print(f"  [{i+1}/{len(remaining_cite_ids)}] Scraping CiteID {cite_id}...", end=' ')

            try:
                case_data = self.scraper.scrape_case(cite_id, court_type, court_db)

                if case_data:
                    batch.append(case_data)
                    self.scraped_cite_ids.add(cite_id)
                    print(f"OK - {case_data['citation']}")
                else:
                    print("FAILED - No data returned")
                    self.failed_cite_ids.append({
                        'cite_id': cite_id,
                        'court': court_name,
                        'error': 'No data returned'
                    })

                # Store batch when full
                if len(batch) >= batch_size:
                    self.store_batch(batch)
                    batch = []

                # Save progress periodically
                if (i + 1) % 50 == 0:
                    self.save_progress()

            except Exception as e:
                print(f"ERROR - {e}")
                self.failed_cite_ids.append({
                    'cite_id': cite_id,
                    'court': court_name,
                    'error': str(e)
                })

            # Rate limiting
            time.sleep(self.scraper.rate_limit_delay)

        # Store remaining batch
        if batch:
            self.store_batch(batch)

        # Save progress after each court
        self.save_progress()

        print(f"\n[OK] Completed {court_name}")

    def store_batch(self, batch: List[Dict]):
        """Store a batch of cases in Supabase"""
        if not batch:
            return

        try:
            stored = self.scraper.store_cases(batch)
            print(f"\n  [STORED] {stored} cases saved to Supabase")
        except Exception as e:
            print(f"\n  [ERROR] Failed to store batch: {e}")
            # Mark all cases in batch as failed
            for case in batch:
                self.failed_cite_ids.append({
                    'cite_id': case['cite_id'],
                    'court': case['court_type'],
                    'error': f'Storage failed: {e}'
                })

    def print_summary(self):
        """Print final scraping summary"""
        print("\n" + "="*60)
        print("SCRAPING SUMMARY")
        print("="*60)
        print(f"Total scraped: {len(self.scraped_cite_ids):,}")
        print(f"Failed: {len(self.failed_cite_ids):,}")
        print(f"Success rate: {len(self.scraped_cite_ids) / (len(self.scraped_cite_ids) + len(self.failed_cite_ids)) * 100:.1f}%")

        if self.failed_cite_ids:
            print(f"\nFailed cases saved to: scraping_failures.json")
            with open('scraping_failures.json', 'w') as f:
                json.dump(self.failed_cite_ids, f, indent=2)

        print("="*60)


def main():
    """Run batch scraper"""
    # Load credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("Environment variables not set, trying config.py...")
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config import SUPABASE_URL, SUPABASE_KEY
            supabase_url = SUPABASE_URL
            supabase_key = SUPABASE_KEY
            print("Loaded credentials from config.py")
        except ImportError as e:
            print(f"ERROR: Could not import from config.py: {e}")
            return
        except Exception as e:
            print(f"ERROR: {e}")
            return

    # Initialize batch scraper
    batch_scraper = BatchCaseScraper(supabase_url, supabase_key)

    # Run scraping
    batch_scraper.scrape_all_cases()


if __name__ == "__main__":
    main()
