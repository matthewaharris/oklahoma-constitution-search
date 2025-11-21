#!/usr/bin/env python3
"""
Oklahoma Constitution Vector Database Builder using Pinecone
"""

import json
import time
import hashlib
import os
from typing import List, Dict, Any
from pathlib import Path

# Import configurations - use environment variables in production
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import *
else:
    try:
        from pinecone_config import *
    except ImportError:
        from config_production import *

from supabase_client import StatutesDatabase

class ConstitutionVectorBuilder:
    def __init__(self):
        self.db = StatutesDatabase()
        self.pinecone_client = None
        self.openai_client = None
        self.index = None

    def install_dependencies(self):
        """Install required packages for vector database"""
        import subprocess
        import sys

        packages = [
            'pinecone-client[grpc]',
            'openai',
            'tiktoken'
        ]

        print("Installing vector database dependencies...")

        for package in packages:
            try:
                # Try to import to see if already installed
                if package == 'pinecone-client[grpc]':
                    import pinecone
                elif package == 'openai':
                    import openai
                elif package == 'tiktoken':
                    import tiktoken
                print(f"[OK] {package} already installed")
            except ImportError:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

    def setup_clients(self):
        """Initialize Pinecone and OpenAI clients"""

        if not OPENAI_API_KEY:
            print("[ERROR] OpenAI API key not set in pinecone_config.py")
            print("Please add your OpenAI API key to the config file")
            return False

        try:
            # Initialize Pinecone
            import pinecone
            from pinecone import Pinecone

            print("Initializing Pinecone client...")
            self.pinecone_client = Pinecone(api_key=PINECONE_API_KEY)

            # Initialize OpenAI
            import openai
            self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

            print("[OK] Clients initialized successfully")
            return True

        except Exception as e:
            print(f"[ERROR] Error initializing clients: {e}")
            return False

    def create_or_get_index(self):
        """Create Pinecone index or connect to existing one"""

        try:
            # Check if index exists
            existing_indexes = self.pinecone_client.list_indexes()
            index_names = [idx.name for idx in existing_indexes]

            if INDEX_NAME in index_names:
                print(f"[OK] Index '{INDEX_NAME}' already exists")
                self.index = self.pinecone_client.Index(INDEX_NAME)

                # Get index stats
                stats = self.index.describe_index_stats()
                print(f"  Current vector count: {stats.total_vector_count}")

                return True

            else:
                print(f"Creating new index: {INDEX_NAME}")

                from pinecone import ServerlessSpec

                self.pinecone_client.create_index(
                    name=INDEX_NAME,
                    dimension=VECTOR_DIMENSION,
                    metric=METRIC,
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )

                # Wait for index to be ready
                print("Waiting for index to be ready...")
                while not self.pinecone_client.describe_index(INDEX_NAME).status['ready']:
                    time.sleep(5)

                self.index = self.pinecone_client.Index(INDEX_NAME)
                print(f"[OK] Index '{INDEX_NAME}' created successfully")
                return True

        except Exception as e:
            print(f"[ERROR] Error with index: {e}")
            return False

    def get_constitution_data(self):
        """Get all constitution sections from the database"""

        print("Fetching constitution data from database...")

        try:
            # Get all constitution records
            result = self.db.client.table('statutes').select(
                'cite_id, section_name, main_text, article_number, section_number, page_title'
            ).eq('title_number', 'CONST').execute()

            constitution_data = result.data

            print(f"[OK] Retrieved {len(constitution_data)} constitution sections")

            # Filter and prepare data
            valid_sections = []
            for section in constitution_data:
                if section.get('main_text') and section['main_text'].strip():
                    valid_sections.append(section)

            print(f"[OK] {len(valid_sections)} sections have valid content")

            return valid_sections

        except Exception as e:
            print(f"[ERROR] Error fetching constitution data: {e}")
            return []

    def chunk_text(self, text: str, max_length: int = MAX_TEXT_LENGTH) -> List[str]:
        """Split long text into chunks for better embeddings"""

        if len(text) <= max_length:
            return [text]

        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space

            if current_length + word_length > max_length:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts using OpenAI"""

        print(f"Creating embeddings for {len(texts)} texts...")

        try:
            response = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts
            )

            embeddings = [data.embedding for data in response.data]

            print(f"[OK] Created {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            print(f"[ERROR] Error creating embeddings: {e}")
            return []

    def prepare_vectors_for_upload(self, sections: List[Dict]) -> List[Dict]:
        """Prepare vectors with metadata for Pinecone upload"""

        print("Preparing vectors for upload...")

        vectors = []

        for section in sections:
            cite_id = section['cite_id']
            main_text = section['main_text']
            section_name = section.get('section_name', '')
            article_number = section.get('article_number', '')
            section_number = section.get('section_number', '')

            # Chunk the text if it's too long
            text_chunks = self.chunk_text(main_text)

            for chunk_idx, chunk in enumerate(text_chunks):
                # Create unique ID for each chunk
                chunk_id = f"{cite_id}"
                if len(text_chunks) > 1:
                    chunk_id += f"_chunk_{chunk_idx}"

                # Create embedding for this chunk
                embeddings = self.create_embeddings([chunk])

                if embeddings:
                    vector_data = {
                        'id': chunk_id,
                        'values': embeddings[0],
                        'metadata': {
                            'cite_id': cite_id,
                            'section_name': section_name,
                            'article_number': str(article_number) if article_number else '',
                            'section_number': str(section_number) if section_number else '',
                            'text': chunk[:1000],  # Store truncated text for reference
                            'chunk_index': chunk_idx,
                            'total_chunks': len(text_chunks),
                            'source': 'oklahoma_constitution'
                        }
                    }

                    vectors.append(vector_data)

                # Small delay to respect rate limits
                time.sleep(0.1)

        print(f"[OK] Prepared {len(vectors)} vectors for upload")
        return vectors

    def upload_vectors_to_pinecone(self, vectors: List[Dict]):
        """Upload vectors to Pinecone in batches"""

        print(f"Uploading {len(vectors)} vectors to Pinecone...")

        total_vectors = len(vectors)
        uploaded_count = 0

        # Upload in batches
        for i in range(0, len(vectors), BATCH_SIZE):
            batch = vectors[i:i + BATCH_SIZE]

            try:
                # Prepare batch for Pinecone
                pinecone_batch = []
                for vector in batch:
                    pinecone_batch.append((
                        vector['id'],
                        vector['values'],
                        vector['metadata']
                    ))

                # Upload batch
                self.index.upsert(vectors=pinecone_batch)

                uploaded_count += len(batch)
                print(f"  Uploaded batch {i//BATCH_SIZE + 1}: {uploaded_count}/{total_vectors} vectors")

                # Small delay between batches
                time.sleep(1)

            except Exception as e:
                print(f"[ERROR] Error uploading batch {i//BATCH_SIZE + 1}: {e}")

        print(f"[OK] Upload completed! {uploaded_count}/{total_vectors} vectors uploaded")

        # Verify upload
        time.sleep(5)  # Wait for indexing
        stats = self.index.describe_index_stats()
        print(f"[OK] Index now contains {stats.total_vector_count} vectors")

    def build_vector_database(self):
        """Main function to build the complete vector database"""

        print("Oklahoma Constitution Vector Database Builder")
        print("=" * 50)

        # Step 1: Install dependencies
        print("\nSTEP 1: Installing dependencies...")
        self.install_dependencies()

        # Step 2: Setup clients
        print("\nSTEP 2: Setting up clients...")
        if not self.setup_clients():
            return False

        # Step 3: Create or connect to index
        print("\nSTEP 3: Setting up Pinecone index...")
        if not self.create_or_get_index():
            return False

        # Step 4: Get constitution data
        print("\nSTEP 4: Getting constitution data...")
        sections = self.get_constitution_data()
        if not sections:
            return False

        # Step 5: Prepare vectors
        print("\nSTEP 5: Creating embeddings and preparing vectors...")
        vectors = self.prepare_vectors_for_upload(sections)
        if not vectors:
            return False

        # Step 6: Upload to Pinecone
        print("\nSTEP 6: Uploading vectors to Pinecone...")
        self.upload_vectors_to_pinecone(vectors)

        print("\n" + "=" * 50)
        print("VECTOR DATABASE BUILD COMPLETED!")
        print("=" * 50)

        return True

def main():
    builder = ConstitutionVectorBuilder()

    # Check configuration
    if not PINECONE_API_KEY:
        print("[ERROR] Pinecone API key not configured")
        return

    if not OPENAI_API_KEY:
        print("[ERROR] OpenAI API key not configured")
        print("Please add your OpenAI API key to pinecone_config.py")
        return

    # Build the vector database
    success = builder.build_vector_database()

    if success:
        print("\n🎉 Vector database ready for semantic search!")
        print("\nNext steps:")
        print("1. Test semantic search with: python test_vector_search.py")
        print("2. Build constitution chat interface")
    else:
        print("\n[ERROR] Vector database build failed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()