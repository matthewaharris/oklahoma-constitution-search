#!/usr/bin/env python3
"""
Simple vector database builder that avoids complex dependencies
Uses OpenAI or a simpler alternative
"""

import json
import time
from typing import List, Dict, Any
from pathlib import Path
import hashlib

from pinecone_config import PINECONE_API_KEY, INDEX_NAME, METRIC
from supabase_client import StatutesDatabase

class SimpleVectorBuilder:
    def __init__(self):
        self.db = StatutesDatabase()
        self.pinecone_client = None
        self.index = None

    def install_minimal_dependencies(self):
        """Install only essential packages"""
        import subprocess
        import sys

        packages = ['pinecone-client']

        print("Installing minimal dependencies...")
        for package in packages:
            try:
                import pinecone
                print(f"✓ {package} already installed")
            except ImportError:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

    def setup_pinecone(self):
        """Setup Pinecone with a fixed dimension"""
        try:
            from pinecone import Pinecone

            print("Setting up Pinecone...")
            self.pinecone_client = Pinecone(api_key=PINECONE_API_KEY)

            # Use a standard dimension that works well
            vector_dimension = 1536  # Standard OpenAI dimension, but we'll create simple vectors

            # Check if index exists
            existing_indexes = self.pinecone_client.list_indexes()
            index_names = [idx.name for idx in existing_indexes]

            if INDEX_NAME not in index_names:
                print(f"Creating index: {INDEX_NAME}")

                from pinecone import ServerlessSpec
                self.pinecone_client.create_index(
                    name=INDEX_NAME,
                    dimension=vector_dimension,
                    metric=METRIC,
                    spec=ServerlessSpec(cloud='aws', region='us-east-1')
                )

                # Wait for index to be ready
                print("Waiting for index to be ready...")
                while not self.pinecone_client.describe_index(INDEX_NAME).status['ready']:
                    time.sleep(5)

            self.index = self.pinecone_client.Index(INDEX_NAME)
            print("✓ Pinecone setup complete")

            return True

        except Exception as e:
            print(f"❌ Error setting up Pinecone: {e}")
            return False

    def create_simple_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create simple word-frequency based embeddings as fallback"""

        print("Creating simple text embeddings...")

        embeddings = []

        for text in texts:
            # Simple approach: create vector based on word frequencies and positions
            words = text.lower().split()

            # Create a simple hash-based vector
            vector = [0.0] * 1536

            for i, word in enumerate(words[:100]):  # Use first 100 words
                # Create a simple hash for each word
                word_hash = hash(word) % 1536
                vector[word_hash] += 1.0 / (i + 1)  # Weight by position

            # Normalize the vector
            magnitude = sum(x*x for x in vector) ** 0.5
            if magnitude > 0:
                vector = [x / magnitude for x in vector]

            embeddings.append(vector)

        return embeddings

    def get_constitution_data(self):
        """Get constitution data from database"""

        print("Fetching constitution data...")

        try:
            result = self.db.client.table('statutes').select(
                'cite_id, section_name, main_text, article_number, section_number'
            ).eq('title_number', 'CONST').execute()

            sections = result.data

            # Filter for sections with content
            valid_sections = [s for s in sections if s.get('main_text') and s['main_text'].strip()]

            print(f"✓ Found {len(valid_sections)} constitution sections")

            return valid_sections

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return []

    def upload_constitution_vectors(self, sections: List[Dict]):
        """Upload constitution sections to Pinecone"""

        print(f"Processing {len(sections)} constitution sections...")

        # Prepare all texts for embedding
        texts = [section['main_text'] for section in sections]

        # Create embeddings
        embeddings = self.create_simple_embeddings(texts)

        if not embeddings:
            print("❌ Failed to create embeddings")
            return False

        # Upload to Pinecone
        vectors_to_upload = []

        for i, (section, embedding) in enumerate(zip(sections, embeddings)):
            vector_data = {
                'id': section['cite_id'],
                'values': embedding,
                'metadata': {
                    'cite_id': section['cite_id'],
                    'section_name': section.get('section_name', ''),
                    'article_number': str(section.get('article_number', '')),
                    'section_number': str(section.get('section_number', '')),
                    'text_preview': section['main_text'][:300],
                    'source': 'oklahoma_constitution'
                }
            }

            vectors_to_upload.append(vector_data)

        # Upload in batches
        batch_size = 50
        uploaded_count = 0

        for i in range(0, len(vectors_to_upload), batch_size):
            batch = vectors_to_upload[i:i+batch_size]

            try:
                # Prepare for Pinecone format
                pinecone_vectors = [
                    (v['id'], v['values'], v['metadata']) for v in batch
                ]

                self.index.upsert(vectors=pinecone_vectors)
                uploaded_count += len(batch)

                print(f"  Uploaded batch {i//batch_size + 1}: {uploaded_count}/{len(vectors_to_upload)}")

                time.sleep(1)  # Small delay

            except Exception as e:
                print(f"❌ Error uploading batch: {e}")

        print(f"✓ Upload completed: {uploaded_count} vectors")

        # Verify
        time.sleep(5)
        stats = self.index.describe_index_stats()
        print(f"✓ Index contains {stats.total_vector_count} total vectors")

        return True

    def build_simple_vector_database(self):
        """Build vector database with minimal dependencies"""

        print("Simple Oklahoma Constitution Vector Database")
        print("=" * 50)

        # Step 1: Install minimal dependencies
        print("\nSTEP 1: Installing minimal dependencies...")
        self.install_minimal_dependencies()

        # Step 2: Setup Pinecone
        print("\nSTEP 2: Setting up Pinecone...")
        if not self.setup_pinecone():
            return False

        # Step 3: Get data
        print("\nSTEP 3: Getting constitution data...")
        sections = self.get_constitution_data()
        if not sections:
            return False

        # Step 4: Upload vectors
        print("\nSTEP 4: Creating embeddings and uploading...")
        if not self.upload_constitution_vectors(sections):
            return False

        print("\n" + "=" * 50)
        print("✅ SIMPLE VECTOR DATABASE COMPLETED!")
        print("=" * 50)
        print("Note: Using simple word-frequency embeddings")
        print("For better quality, consider using OpenAI API")

        return True

def main():
    if not PINECONE_API_KEY:
        print("❌ Pinecone API key not configured")
        return

    print("Choose embedding approach:")
    print("1. Simple embeddings (no external dependencies)")
    print("2. Try OpenAI (requires API key)")
    print("3. Exit")

    choice = input("Enter choice (1-3): ").strip()

    if choice == '1':
        builder = SimpleVectorBuilder()
        builder.build_simple_vector_database()

    elif choice == '2':
        api_key = input("Enter OpenAI API key: ").strip()
        if api_key:
            # Use the original OpenAI approach
            print("Using OpenAI embeddings...")
            try:
                import openai
                # Use original vector builder with OpenAI
                from vector_database_builder import ConstitutionVectorBuilder
                builder = ConstitutionVectorBuilder()
                builder.build_vector_database()
            except ImportError:
                print("Installing openai...")
                import subprocess
                import sys
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openai'])
                print("Please run again and choose option 2")
        else:
            print("❌ API key required for OpenAI")

    elif choice == '3':
        print("Goodbye!")

    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()