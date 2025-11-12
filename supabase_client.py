#!/usr/bin/env python3
"""
Supabase client for Oklahoma Statutes Database
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("Warning: supabase-py not installed. Run: pip install supabase")
    SUPABASE_AVAILABLE = False

# Try to import configuration
try:
    from config import SUPABASE_URL, SUPABASE_KEY, SCRAPER_VERSION
except ImportError:
    print("Warning: config.py not found. Using environment variables or defaults.")
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
    SCRAPER_VERSION = os.getenv('SCRAPER_VERSION', '1.0')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatutesDatabase:
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """Initialize the database client"""
        if not SUPABASE_AVAILABLE:
            raise ImportError("supabase-py is required. Install with: pip install supabase")

        self.url = supabase_url or SUPABASE_URL
        self.key = supabase_key or SUPABASE_KEY

        if not self.url or not self.key:
            raise ValueError("Supabase URL and key are required. Check config.py or environment variables.")

        self.client: Client = create_client(self.url, self.key)
        logger.info("Supabase client initialized successfully")

    def insert_statute(self, statute_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a complete statute with all related data
        """
        try:
            # Prepare main statute record
            statute_record = {
                'cite_id': statute_data['cite_id'],
                'url': statute_data['url'],
                'title_number': statute_data['metadata'].get('title_number'),
                'title_name': statute_data['metadata'].get('title_name'),
                'chapter_number': statute_data['metadata'].get('chapter_number'),
                'chapter_name': statute_data['metadata'].get('chapter_name'),
                'article_number': statute_data['metadata'].get('article_number'),
                'article_name': statute_data['metadata'].get('article_name'),
                'section_number': statute_data['metadata'].get('section_number'),
                'section_name': statute_data['metadata'].get('section_name'),
                'page_title': statute_data['metadata'].get('page_title'),
                'title_bar': statute_data['metadata'].get('title_bar'),
                'citation_format': statute_data['metadata'].get('citation_format'),
                'main_text': statute_data['content'].get('main_text'),
                'full_json': statute_data,
                'scraper_version': statute_data.get('scraper_version', SCRAPER_VERSION)
            }

            # Insert main statute record
            result = self.client.table('statutes').insert(statute_record).execute()

            if not result.data:
                raise Exception("Failed to insert statute record")

            statute_id = result.data[0]['id']
            logger.info(f"Inserted statute {statute_data['cite_id']} with ID {statute_id}")

            # Insert paragraphs
            if 'paragraphs' in statute_data['content']:
                self._insert_paragraphs(statute_id, statute_data['content']['paragraphs'])

            # Insert definitions
            if 'definitions' in statute_data['content']:
                self._insert_definitions(statute_id, statute_data['content']['definitions'])

            # Insert legislative history
            if 'historical_data' in statute_data['content']:
                self._insert_legislative_history(statute_id, statute_data['content']['historical_data'])

            # Insert citations
            if 'citations' in statute_data and statute_data['citations'].get('references'):
                self._insert_citations(statute_id, statute_data['citations']['references'])

            # Insert superseded documents
            if 'superseded_documents' in statute_data['content']:
                self._insert_superseded_documents(statute_id, statute_data['content']['superseded_documents'])

            return {
                'success': True,
                'statute_id': statute_id,
                'cite_id': statute_data['cite_id']
            }

        except Exception as e:
            logger.error(f"Error inserting statute {statute_data.get('cite_id', 'unknown')}: {e}")
            return {
                'success': False,
                'error': str(e),
                'cite_id': statute_data.get('cite_id', 'unknown')
            }

    def _insert_paragraphs(self, statute_id: str, paragraphs: List[Dict[str, Any]]):
        """Insert statute paragraphs"""
        paragraph_records = []
        for i, paragraph in enumerate(paragraphs, 1):
            paragraph_records.append({
                'statute_id': statute_id,
                'paragraph_number': i,
                'text': paragraph.get('text', ''),
                'is_historical': paragraph.get('is_historical', False)
            })

        if paragraph_records:
            result = self.client.table('statute_paragraphs').insert(paragraph_records).execute()
            logger.info(f"Inserted {len(paragraph_records)} paragraphs for statute {statute_id}")

    def _insert_definitions(self, statute_id: str, definitions: List[Dict[str, Any]]):
        """Insert statute definitions"""
        definition_records = []
        for definition in definitions:
            definition_records.append({
                'statute_id': statute_id,
                'definition_number': definition.get('number', ''),
                'term': definition.get('term', ''),
                'definition': definition.get('definition', '')
            })

        if definition_records:
            result = self.client.table('statute_definitions').insert(definition_records).execute()
            logger.info(f"Inserted {len(definition_records)} definitions for statute {statute_id}")

    def _insert_legislative_history(self, statute_id: str, historical_data: Dict[str, Any]):
        """Insert legislative history"""
        if 'legislative_history' not in historical_data:
            return

        history_records = []
        for entry in historical_data['legislative_history']:
            # Parse bill information
            bill_type = None
            bill_number = None
            if 'bill' in entry:
                bill_parts = entry['bill'].split(' ', 1)
                if len(bill_parts) == 2:
                    bill_type = bill_parts[0]  # HB, SB, etc.
                    bill_number = bill_parts[1]

            history_records.append({
                'statute_id': statute_id,
                'year': int(entry.get('year', 0)),
                'bill_type': bill_type,
                'bill_number': bill_number,
                'details': entry.get('details', ''),
                'effective_date': None  # Could be extracted from details if needed
            })

        if history_records:
            result = self.client.table('legislative_history').insert(history_records).execute()
            logger.info(f"Inserted {len(history_records)} legislative history entries for statute {statute_id}")

    def _insert_citations(self, statute_id: str, citations: List[Dict[str, Any]]):
        """Insert statute citations"""
        citation_records = []
        for citation in citations:
            citation_records.append({
                'statute_id': statute_id,
                'cited_statute_cite_id': None,  # Could be extracted from href if needed
                'citation_text': citation.get('cite', ''),
                'citation_name': citation.get('name', ''),
                'citation_level': citation.get('level', ''),
                'href': citation.get('cite_href') or citation.get('name_href')
            })

        if citation_records:
            result = self.client.table('statute_citations').insert(citation_records).execute()
            logger.info(f"Inserted {len(citation_records)} citations for statute {statute_id}")

    def _insert_superseded_documents(self, statute_id: str, superseded_docs: List[Dict[str, Any]]):
        """Insert superseded document references"""
        superseded_records = []
        for doc in superseded_docs:
            superseded_records.append({
                'statute_id': statute_id,
                'superseded_cite_id': None,  # Could be extracted from href
                'text': doc.get('text', ''),
                'href': doc.get('href', '')
            })

        if superseded_records:
            result = self.client.table('superseded_documents').insert(superseded_records).execute()
            logger.info(f"Inserted {len(superseded_records)} superseded documents for statute {statute_id}")

    def get_statute(self, cite_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a statute by cite_id"""
        try:
            result = self.client.table('statutes').select('*').eq('cite_id', cite_id).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error retrieving statute {cite_id}: {e}")
            return None

    def statute_exists(self, cite_id: str) -> bool:
        """Check if a statute already exists in the database"""
        try:
            result = self.client.table('statutes').select('cite_id').eq('cite_id', cite_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking if statute {cite_id} exists: {e}")
            return False

    def get_statutes_by_title(self, title_number: str) -> List[Dict[str, Any]]:
        """Get all statutes for a specific title"""
        try:
            result = self.client.table('statutes').select('*').eq('title_number', title_number).order('chapter_number', 'section_number').execute()
            return result.data
        except Exception as e:
            logger.error(f"Error retrieving statutes for title {title_number}: {e}")
            return []

    def search_statutes(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search statutes by text content"""
        try:
            # Use PostgreSQL full-text search
            result = self.client.table('statutes').select('cite_id, title_number, section_name, main_text').text_search('main_text', search_term).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error searching statutes for '{search_term}': {e}")
            return []

    def get_database_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the database"""
        try:
            stats = {}

            # Total statutes
            result = self.client.table('statutes').select('id', count='exact').execute()
            stats['total_statutes'] = result.count if hasattr(result, 'count') else 0

            # Statutes by title
            result = self.client.table('statutes').select('title_number').execute()
            titles = {}
            for statute in result.data:
                title = statute.get('title_number', 'Unknown')
                titles[title] = titles.get(title, 0) + 1
            stats['statutes_by_title'] = titles

            # Total definitions
            result = self.client.table('statute_definitions').select('id', count='exact').execute()
            stats['total_definitions'] = result.count if hasattr(result, 'count') else 0

            return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}

def test_database_connection():
    """Test the database connection and basic operations"""
    try:
        db = StatutesDatabase()

        # Test connection
        stats = db.get_database_stats()
        print(f"Database connection successful!")
        print(f"Database stats: {stats}")

        return True

    except Exception as e:
        print(f"Database connection failed: {e}")
        print("\nPlease ensure:")
        print("1. You have created config.py with your Supabase credentials")
        print("2. You have installed supabase-py: pip install supabase")
        print("3. Your Supabase URL and key are correct")
        return False

if __name__ == "__main__":
    test_database_connection()