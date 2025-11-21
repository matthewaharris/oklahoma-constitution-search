"""
Generate embeddings for all Oklahoma legal documents and upload to Pinecone
Uses OpenAI text-embedding-3-small for cost-effective, high-quality embeddings
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from openai import OpenAI
from pinecone import Pinecone
from supabase import create_client, Client

# Import configuration
import pinecone_config

# Load credentials
try:
    import config
    SUPABASE_URL = config.SUPABASE_URL
    SUPABASE_KEY = config.SUPABASE_KEY
except ImportError:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize clients
openai_client = OpenAI(api_key=pinecone_config.OPENAI_API_KEY)
pc = Pinecone(api_key=pinecone_config.PINECONE_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuration
BATCH_SIZE = 100  # Process 100 documents at a time
EMBEDDING_BATCH_SIZE = 2048  # OpenAI allows up to 2048 inputs per request
PROGRESS_FILE = "embedding_progress.json"

class EmbeddingGenerator:
    """Generate and upload embeddings to Pinecone"""

    def __init__(self):
        self.progress = self._load_progress()
        self.constitution_index = pc.Index('oklahoma-constitution')
        self.statutes_index = pc.Index('oklahoma-statutes')

    def _load_progress(self) -> Dict:
        """Load progress from file"""
        if Path(PROGRESS_FILE).exists():
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        return {
            'processed_ids': [],
            'failed_ids': [],
            'total_processed': 0,
            'total_cost': 0.0
        }

    def _save_progress(self):
        """Save progress to file"""
        self.progress['last_updated'] = datetime.now().isoformat()
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def fetch_documents_batch(self, offset: int, limit: int) -> List[Dict]:
        """Fetch a batch of documents from Supabase"""
        response = supabase.table('statutes')\
            .select('cite_id, document_type, page_title, title_number, section_number, article_number, main_text')\
            .range(offset, offset + limit - 1)\
            .execute()
        return response.data if response.data else []

    def prepare_text_for_embedding(self, doc: Dict) -> str:
        """Prepare document text for embedding"""
        # Create a rich text representation
        parts = []

        # Add document type
        doc_type = doc.get('document_type', 'statute')
        parts.append(f"Document type: {doc_type}")

        # Add title/article
        if doc_type == 'constitution':
            if doc.get('article_number'):
                parts.append(f"Article: {doc['article_number']}")
        else:
            if doc.get('title_number'):
                parts.append(f"Title: {doc['title_number']}")

        # Add section
        if doc.get('section_number'):
            parts.append(f"Section: {doc['section_number']}")

        # Add page title
        if doc.get('page_title'):
            parts.append(f"Title: {doc['page_title']}")

        # Add main text (truncate if too long)
        main_text = doc.get('main_text', '')
        if len(main_text) > pinecone_config.MAX_TEXT_LENGTH:
            main_text = main_text[:pinecone_config.MAX_TEXT_LENGTH] + "..."
        parts.append(f"\nContent:\n{main_text}")

        return "\n".join(parts)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        try:
            response = openai_client.embeddings.create(
                model=pinecone_config.EMBEDDING_MODEL,
                input=texts
            )

            # Calculate cost (text-embedding-3-small: $0.00002 per 1K tokens, ~750 tokens per doc average)
            # Rough estimate: ~0.00002 * (number of texts)
            estimated_cost = len(texts) * 0.00002
            self.progress['total_cost'] += estimated_cost

            return [item.embedding for item in response.data]

        except Exception as e:
            print(f"Error generating embeddings: {e}")
            raise

    def prepare_vectors(self, documents: List[Dict], embeddings: List[List[float]]) -> tuple:
        """Prepare vectors for Pinecone upsert, separated by index"""
        constitution_vectors = []
        statutes_vectors = []

        for doc, embedding in zip(documents, embeddings):
            cite_id = doc['cite_id']
            doc_type = doc.get('document_type', 'statute')

            # Prepare metadata
            metadata = {
                'cite_id': cite_id,
                'document_type': doc_type,
                'page_title': doc.get('page_title', ''),
                'section_number': doc.get('section_number', ''),
            }

            # Add type-specific metadata
            if doc_type == 'constitution':
                metadata['article_number'] = doc.get('article_number', '')
            else:
                metadata['title_number'] = doc.get('title_number', '')

            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v is not None and v != ''}

            vector = {
                'id': cite_id,
                'values': embedding,
                'metadata': metadata
            }

            # Route to appropriate index
            if doc_type == 'constitution':
                constitution_vectors.append(vector)
            else:
                statutes_vectors.append(vector)

        return constitution_vectors, statutes_vectors

    def upload_to_pinecone(self, constitution_vectors: List, statutes_vectors: List):
        """Upload vectors to appropriate Pinecone indexes"""
        if constitution_vectors:
            self.constitution_index.upsert(vectors=constitution_vectors)

        if statutes_vectors:
            self.statutes_index.upsert(vectors=statutes_vectors)

    def process_all_documents(self):
        """Main processing function"""
        print("=" * 70)
        print("GENERATING EMBEDDINGS FOR OKLAHOMA LEGAL DOCUMENTS")
        print("=" * 70)
        print(f"\nModel: {pinecone_config.EMBEDDING_MODEL}")
        print(f"Target: {BATCH_SIZE} documents per batch")

        # Get total count
        total_response = supabase.table('statutes').select('*', count='exact').limit(1).execute()
        total_docs = total_response.count

        print(f"Total documents: {total_docs:,}")

        if self.progress['processed_ids']:
            print(f"Resuming from previous run...")
            print(f"Already processed: {len(self.progress['processed_ids']):,} documents")

        offset = 0
        processed_count = 0
        failed_count = 0

        while offset < total_docs:
            # Fetch batch
            documents = self.fetch_documents_batch(offset, BATCH_SIZE)

            if not documents:
                break

            # Filter out already processed
            documents = [d for d in documents if d['cite_id'] not in self.progress['processed_ids']]

            if not documents:
                offset += BATCH_SIZE
                continue

            # Prepare texts for embedding
            texts = [self.prepare_text_for_embedding(doc) for doc in documents]

            try:
                # Generate embeddings
                embeddings = self.generate_embeddings(texts)

                # Prepare vectors
                constitution_vecs, statutes_vecs = self.prepare_vectors(documents, embeddings)

                # Upload to Pinecone
                self.upload_to_pinecone(constitution_vecs, statutes_vecs)

                # Track progress
                for doc in documents:
                    self.progress['processed_ids'].append(doc['cite_id'])

                processed_count += len(documents)
                self.progress['total_processed'] = processed_count

                # Save progress
                self._save_progress()

                # Progress update
                progress_pct = ((offset + len(documents)) / total_docs) * 100
                print(f"Progress: {offset + len(documents):,}/{total_docs:,} ({progress_pct:.1f}%) | "
                      f"Processed: {processed_count:,} | Failed: {failed_count} | "
                      f"Cost: ${self.progress['total_cost']:.4f}")

            except Exception as e:
                print(f"Error processing batch at offset {offset}: {e}")
                for doc in documents:
                    self.progress['failed_ids'].append(doc['cite_id'])
                failed_count += len(documents)

            offset += BATCH_SIZE

            # Rate limiting - avoid hitting OpenAI rate limits
            time.sleep(0.1)

        # Final summary
        print("\n" + "=" * 70)
        print("EMBEDDING GENERATION COMPLETE")
        print("=" * 70)
        print(f"Total processed: {processed_count:,}")
        print(f"Total failed: {failed_count}")
        print(f"Total cost: ${self.progress['total_cost']:.2f}")

        # Verify indexes
        print("\n" + "=" * 70)
        print("PINECONE INDEX VERIFICATION")
        print("=" * 70)

        const_stats = self.constitution_index.describe_index_stats()
        stat_stats = self.statutes_index.describe_index_stats()

        print(f"Constitution index: {const_stats.total_vector_count:,} vectors")
        print(f"Statutes index: {stat_stats.total_vector_count:,} vectors")
        print(f"Total in Pinecone: {const_stats.total_vector_count + stat_stats.total_vector_count:,}")

        print("\nDone!")


def main():
    generator = EmbeddingGenerator()
    generator.process_all_documents()


if __name__ == "__main__":
    main()
