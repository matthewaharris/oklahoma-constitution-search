#!/usr/bin/env python3
"""
Batch AG Opinion Scraper
Scrapes all discovered AG opinions and stores them in Supabase
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

from scrapers.ag_opinion_scraper import AGOpinionScraper

class BatchAGOpinionScraper:
    """Batch scrape all discovered AG opinions"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.scraper = AGOpinionScraper(supabase_url, supabase_key)
        self.progress_file = "ag_scraping_progress.json"
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

    def scrape_all_opinions(self, discovered_opinions_file: str = "discovered_ag_opinions.json"):
        """
        Scrape all AG opinions from discovery file

        Args:
            discovered_opinions_file: Path to discovered_ag_opinions.json
        """
        # Load discovered opinions
        print("="*60)
        print("Oklahoma AG Opinion Batch Scraper")
        print("="*60)

        with open(discovered_opinions_file, 'r') as f:
            discovered_data = json.load(f)

        cite_ids = discovered_data['cite_ids']

        # Count total opinions
        total_opinions = len(cite_ids)
        already_scraped = len(self.scraped_cite_ids)
        remaining = total_opinions - already_scraped

        print(f"\nTotal AG opinions to scrape: {total_opinions}")
        print(f"Already scraped: {already_scraped}")
        print(f"Remaining: {remaining}")
        print(f"Estimated time: {remaining * 2 / 60:.0f}-{remaining * 3 / 60:.0f} minutes")
        print("="*60)

        # Filter out already scraped opinions
        remaining_cite_ids = [cid for cid in cite_ids if cid not in self.scraped_cite_ids]

        if not remaining_cite_ids:
            print(f"[SKIP] All {len(cite_ids)} opinions already scraped\n")
            self.print_summary()
            return

        print(f"\nOpinions to scrape: {len(remaining_cite_ids)}/{len(cite_ids)}\n")

        batch = []
        batch_size = 10  # Store in batches

        for i, cite_id in enumerate(remaining_cite_ids):
            print(f"  [{i+1}/{len(remaining_cite_ids)}] Scraping CiteID {cite_id}...", end=' ')

            try:
                opinion_data = self.scraper.scrape_opinion(cite_id)

                if opinion_data:
                    batch.append(opinion_data)
                    self.scraped_cite_ids.add(cite_id)
                    print(f"OK - {opinion_data['citation']}")
                else:
                    print("FAILED - No data returned")
                    self.failed_cite_ids.append({
                        'cite_id': cite_id,
                        'error': 'No data returned'
                    })

                # Store batch when full
                if len(batch) >= batch_size:
                    self.store_batch(batch)
                    batch = []

                # Save progress periodically
                if (i + 1) % 20 == 0:
                    self.save_progress()

            except Exception as e:
                print(f"ERROR - {e}")
                self.failed_cite_ids.append({
                    'cite_id': cite_id,
                    'error': str(e)
                })

            # Rate limiting
            time.sleep(self.scraper.rate_limit_delay)

        # Store remaining batch
        if batch:
            self.store_batch(batch)

        # Save final progress
        self.save_progress()

        # Print summary
        self.print_summary()

    def store_batch(self, batch: List[Dict]):
        """Store a batch of AG opinions in Supabase"""
        if not batch:
            return

        try:
            stored = self.scraper.store_opinions(batch)
            print(f"\n  [STORED] {stored} opinions saved to Supabase")
        except Exception as e:
            print(f"\n  [ERROR] Failed to store batch: {e}")
            # Mark all opinions in batch as failed
            for opinion in batch:
                self.failed_cite_ids.append({
                    'cite_id': opinion['cite_id'],
                    'error': f'Storage failed: {e}'
                })

    def print_summary(self):
        """Print final scraping summary"""
        print("\n" + "="*60)
        print("SCRAPING SUMMARY")
        print("="*60)
        print(f"Total scraped: {len(self.scraped_cite_ids)}")
        print(f"Failed: {len(self.failed_cite_ids)}")
        if len(self.scraped_cite_ids) + len(self.failed_cite_ids) > 0:
            print(f"Success rate: {len(self.scraped_cite_ids) / (len(self.scraped_cite_ids) + len(self.failed_cite_ids)) * 100:.1f}%")

        if self.failed_cite_ids:
            print(f"\nFailed opinions saved to: ag_scraping_failures.json")
            with open('ag_scraping_failures.json', 'w') as f:
                json.dump(self.failed_cite_ids, f, indent=2)

        print("="*60)


def main():
    """Run batch AG opinion scraper"""
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
    batch_scraper = BatchAGOpinionScraper(supabase_url, supabase_key)

    # Run scraping
    batch_scraper.scrape_all_opinions()


if __name__ == "__main__":
    main()
