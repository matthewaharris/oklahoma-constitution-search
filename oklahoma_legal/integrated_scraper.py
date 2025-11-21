#!/usr/bin/env python3
"""
Integrated Oklahoma Statutes Scraper with Supabase Database Storage
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any

# Import our existing scraper and database classes
from final_oklahoma_scraper import FinalOklahomaStatutesScraper
from supabase_client import StatutesDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegratedStatutesScraper:
    def __init__(self, delay_seconds: float = 1.0):
        """Initialize the integrated scraper with database connection"""
        self.scraper = FinalOklahomaStatutesScraper()
        self.database = StatutesDatabase()
        self.delay_seconds = delay_seconds

        logger.info("Integrated scraper initialized with database connection")

    def scrape_and_store_statute(self, cite_id: str, force_update: bool = False) -> Dict[str, Any]:
        """
        Scrape a single statute and store it in the database

        Args:
            cite_id: The OSCN cite ID for the statute
            force_update: If True, update even if statute already exists

        Returns:
            Dictionary with operation result
        """
        result = {
            'cite_id': cite_id,
            'success': False,
            'action': None,
            'error': None
        }

        try:
            # Check if statute already exists (unless force update)
            if not force_update and self.database.statute_exists(cite_id):
                result['action'] = 'skipped'
                result['success'] = True
                result['message'] = f"Statute {cite_id} already exists in database"
                logger.info(f"Skipping {cite_id} - already exists")
                return result

            # Scrape the statute
            logger.info(f"Scraping statute {cite_id}")
            statute_data = self.scraper.scrape_statute(cite_id)

            if not statute_data:
                result['error'] = "Failed to scrape statute data"
                logger.error(f"Failed to scrape statute {cite_id}")
                return result

            # Store in database
            logger.info(f"Storing statute {cite_id} in database")
            db_result = self.database.insert_statute(statute_data)

            if db_result['success']:
                result['success'] = True
                result['action'] = 'inserted'
                result['statute_id'] = db_result['statute_id']
                result['message'] = f"Successfully scraped and stored statute {cite_id}"
                logger.info(f"Successfully stored statute {cite_id} with ID {db_result['statute_id']}")
            else:
                result['error'] = db_result['error']
                logger.error(f"Failed to store statute {cite_id}: {db_result['error']}")

            # Add delay to be respectful to the server
            time.sleep(self.delay_seconds)

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error processing statute {cite_id}: {e}")

        return result

    def bulk_scrape_statutes(self, cite_ids: List[str], force_update: bool = False) -> Dict[str, Any]:
        """
        Scrape multiple statutes in bulk

        Args:
            cite_ids: List of cite IDs to scrape
            force_update: If True, update even if statutes already exist

        Returns:
            Summary of bulk operation
        """
        start_time = time.time()
        results = {
            'total_requested': len(cite_ids),
            'successful': 0,
            'skipped': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }

        logger.info(f"Starting bulk scrape of {len(cite_ids)} statutes")

        for i, cite_id in enumerate(cite_ids, 1):
            logger.info(f"Processing {i}/{len(cite_ids)}: {cite_id}")

            result = self.scrape_and_store_statute(cite_id, force_update)
            results['details'].append(result)

            if result['success']:
                if result['action'] == 'skipped':
                    results['skipped'] += 1
                else:
                    results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'cite_id': cite_id,
                    'error': result['error']
                })

            # Progress update every 10 items
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(cite_ids)} - Success: {results['successful']}, Skipped: {results['skipped']}, Failed: {results['failed']}")

        elapsed_time = time.time() - start_time
        results['elapsed_seconds'] = elapsed_time
        results['average_time_per_statute'] = elapsed_time / len(cite_ids)

        logger.info(f"Bulk scrape completed in {elapsed_time:.2f} seconds")
        logger.info(f"Results: {results['successful']} successful, {results['skipped']} skipped, {results['failed']} failed")

        return results

    def scrape_title_range(self, title_number: str, start_cite_id: int, end_cite_id: int, force_update: bool = False) -> Dict[str, Any]:
        """
        Scrape a range of cite IDs for testing or systematic collection

        Args:
            title_number: The title number for context
            start_cite_id: Starting cite ID (inclusive)
            end_cite_id: Ending cite ID (inclusive)
            force_update: If True, update even if statutes already exist

        Returns:
            Summary of range operation
        """
        cite_ids = [str(i) for i in range(start_cite_id, end_cite_id + 1)]
        logger.info(f"Scraping cite ID range {start_cite_id}-{end_cite_id} for Title {title_number}")

        return self.bulk_scrape_statutes(cite_ids, force_update)

    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get statistics about what's been scraped"""
        return self.database.get_database_stats()

    def export_scraped_data(self, output_file: str, title_number: str = None) -> bool:
        """
        Export scraped data to a JSON file

        Args:
            output_file: Path to output file
            title_number: If specified, only export this title

        Returns:
            True if successful, False otherwise
        """
        try:
            if title_number:
                statutes = self.database.get_statutes_by_title(title_number)
                logger.info(f"Exporting {len(statutes)} statutes from Title {title_number}")
            else:
                # This would need a method to get all statutes
                logger.warning("Full database export not implemented yet")
                return False

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(statutes, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"Data exported to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False

def test_integrated_scraper():
    """Test the integrated scraper with a few known statutes"""
    try:
        scraper = IntegratedStatutesScraper(delay_seconds=2.0)

        # Test with our known working statute
        test_cite_ids = [
            '440462',  # Our test statute
            # Add more test cite IDs here if you have them
        ]

        print("Testing integrated scraper...")
        print("="*60)

        # Test single statute
        for cite_id in test_cite_ids:
            print(f"\nTesting statute {cite_id}:")
            result = scraper.scrape_and_store_statute(cite_id)

            if result['success']:
                print(f"✓ {result['action'].title()}: {result['message']}")
                if 'statute_id' in result:
                    print(f"  Database ID: {result['statute_id']}")
            else:
                print(f"✗ Failed: {result['error']}")

        # Show database stats
        print(f"\nDatabase Statistics:")
        stats = scraper.get_scraping_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\nIntegrated scraper test completed!")

    except Exception as e:
        print(f"Error testing integrated scraper: {e}")
        print("\nPlease ensure:")
        print("1. config.py is set up with valid Supabase credentials")
        print("2. Database schema has been created in Supabase")
        print("3. supabase-py is installed: pip install supabase")

if __name__ == "__main__":
    test_integrated_scraper()