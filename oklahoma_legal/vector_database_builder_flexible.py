#!/usr/bin/env python3
"""
Flexible Oklahoma Constitution Vector Database Builder
Works with multiple embedding providers (OpenAI, HuggingFace, Cohere)
"""

import json
import time
from typing import List, Dict, Any
from pathlib import Path

from pinecone_config import PINECONE_API_KEY, INDEX_NAME, METRIC
from supabase_client import StatutesDatabase
from embedding_options import EmbeddingFactory, EmbeddingProvider

class FlexibleVectorBuilder:
    def __init__(self):
        self.db = StatutesDatabase()
        self.pinecone_client = None
        self.embedding_provider = None
        self.index = None

    def install_dependencies(self):
        """Install required packages"""
        import subprocess
        import sys

        packages = ['pinecone-client[grpc]']

        print("Installing base dependencies...")
        for package in packages:
            try:
                import pinecone
                print(f"✓ {package} already installed")
            except ImportError:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

    def setup_embedding_provider(self) -> bool:
        """Set up embedding provider"""

        print("Setting up embedding provider...")

        # Try to load saved provider config
        config_file = Path('selected_embedding_provider.json')
        if config_file.exists():
            print("Found saved provider configuration")
            response = input("Use saved configuration? (y/n): ").lower()
            if response == 'y':
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"Using saved provider: {config['provider_type']}")

        # Manual provider selection
        print("\nChoose embedding provider:")
        print("1. HuggingFace (FREE) - Recommended for testing")
        print("2. OpenAI (Requires API key)")
        print("3. Cohere (Requires API key)")

        choice = input("Enter choice (1-3): ").strip()

        try:
            if choice == '1':
                print("Using HuggingFace sentence-transformers (FREE)")
                self.embedding_provider = EmbeddingFactory.create_provider("huggingface")

            elif choice == '2':
                api_key = input("Enter OpenAI API key: ").strip()
                if not api_key:
                    print("❌ API key required")
                    return False
                self.embedding_provider = EmbeddingFactory.create_provider("openai", api_key=api_key)

            elif choice == '3':
                api_key = input("Enter Cohere API key: ").strip()
                if not api_key:
                    print("❌ API key required")
                    return False
                self.embedding_provider = EmbeddingFactory.create_provider("cohere", api_key=api_key)

            else:
                print("❌ Invalid choice")
                return False

            print(f"✓ Embedding provider setup complete")
            print(f"  Vector dimension: {self.embedding_provider.get_dimension()}")

            return True

        except Exception as e:
            print(f"❌ Error setting up embedding provider: {e}")
            return False

    def setup_pinecone(self) -> bool:
        """Initialize Pinecone client and index"""

        try:
            from pinecone import Pinecone

            print("Setting up Pinecone...")
            self.pinecone_client = Pinecone(api_key=PINECONE_API_KEY)

            # Get the actual dimension from our embedding provider
            vector_dimension = self.embedding_provider.get_dimension()

            # Check if index exists
            existing_indexes = self.pinecone_client.list_indexes()
            index_names = [idx.name for idx in existing_indexes]

            if INDEX_NAME in index_names:
                print(f"✓ Index '{INDEX_NAME}' already exists")

                # Check if dimension matches
                index_info = self.pinecone_client.describe_index(INDEX_NAME)
                existing_dimension = index_info.dimension

                if existing_dimension != vector_dimension:
                    print(f"⚠️ Dimension mismatch!")
                    print(f"   Index has dimension {existing_dimension}")
                    print(f"   Provider needs dimension {vector_dimension}")
                    print(f"   You may need to delete and recreate the index")

                    response = input("Delete and recreate index? (y/n): ").lower()
                    if response == 'y':
                        print("Deleting existing index...")
                        self.pinecone_client.delete_index(INDEX_NAME)
                        time.sleep(10)  # Wait for deletion

                        print("Creating new index...")
                        from pinecone import ServerlessSpec
                        self.pinecone_client.create_index(
                            name=INDEX_NAME,
                            dimension=vector_dimension,
                            metric=METRIC,
                            spec=ServerlessSpec(cloud='aws', region='us-east-1')
                        )

                        # Wait for ready
                        while not self.pinecone_client.describe_index(INDEX_NAME).status['ready']:
                            time.sleep(5)

                self.index = self.pinecone_client.Index(INDEX_NAME)

            else:
                print(f"Creating new index: {INDEX_NAME}")

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

            print(f"✓ Pinecone index ready")

            # Get current stats
            stats = self.index.describe_index_stats()
            print(f"  Current vectors: {stats.total_vector_count}")

            return True

        except Exception as e:
            print(f"❌ Error setting up Pinecone: {e}")
            return False

    def get_constitution_data(self):
        """Get constitution data from database"""

        print("Fetching constitution data...")

        try:
            result = self.db.client.table('statutes').select(
                'cite_id, section_name, main_text, article_number, section_number, page_title'
            ).eq('title_number', 'CONST').execute()

            sections = result.data

            # Filter for sections with content
            valid_sections = [s for s in sections if s.get('main_text') and s['main_text'].strip()]

            print(f"✓ Found {len(valid_sections)} constitution sections with content")

            return valid_sections

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return []

    def process_and_upload_vectors(self, sections: List[Dict]):
        """Process sections and upload to Pinecone"""

        print(f"Processing {len(sections)} constitution sections...")

        total_uploaded = 0

        for section in sections:
            try:
                cite_id = section['cite_id']
                main_text = section['main_text']
                section_name = section.get('section_name', '')

                print(f"  Processing {cite_id}: {section_name[:50]}...")

                # Create embedding
                embeddings = self.embedding_provider.create_embeddings([main_text])

                if not embeddings:
                    print(f"    ❌ Failed to create embedding")
                    continue

                # Prepare vector for Pinecone
                vector_data = {
                    'id': cite_id,
                    'values': embeddings[0],
                    'metadata': {
                        'cite_id': cite_id,
                        'section_name': section_name,
                        'article_number': str(section.get('article_number', '')),
                        'section_number': str(section.get('section_number', '')),
                        'text_preview': main_text[:500],  # First 500 chars for preview
                        'source': 'oklahoma_constitution'
                    }
                }

                # Upload to Pinecone
                self.index.upsert(vectors=[vector_data])

                total_uploaded += 1
                print(f"    ✓ Uploaded")

                # Small delay to be respectful
                time.sleep(0.5)

            except Exception as e:
                print(f"    ❌ Error processing {cite_id}: {e}")

        print(f"\n✓ Upload completed: {total_uploaded}/{len(sections)} vectors")

        # Verify final count
        time.sleep(5)
        stats = self.index.describe_index_stats()
        print(f"✓ Index now contains {stats.total_vector_count} total vectors")

    def build_vector_database(self):
        """Main function to build vector database"""

        print("Flexible Oklahoma Constitution Vector Database Builder")
        print("=" * 60)

        # Step 1: Install dependencies
        print("\nSTEP 1: Installing dependencies...")
        self.install_dependencies()

        # Step 2: Setup embedding provider
        print("\nSTEP 2: Setting up embedding provider...")
        if not self.setup_embedding_provider():
            return False

        # Step 3: Setup Pinecone
        print("\nSTEP 3: Setting up Pinecone...")
        if not self.setup_pinecone():
            return False

        # Step 4: Get data
        print("\nSTEP 4: Getting constitution data...")
        sections = self.get_constitution_data()
        if not sections:
            return False

        # Step 5: Process and upload
        print("\nSTEP 5: Creating embeddings and uploading to Pinecone...")
        self.process_and_upload_vectors(sections)

        print("\n" + "=" * 60)
        print("🎉 VECTOR DATABASE BUILD COMPLETED!")
        print("=" * 60)
        print(f"✓ Using embedding provider: {type(self.embedding_provider).__name__}")
        print(f"✓ Vector dimension: {self.embedding_provider.get_dimension()}")
        print(f"✓ Index name: {INDEX_NAME}")

        return True

def main():
    if not PINECONE_API_KEY:
        print("❌ Pinecone API key not configured in pinecone_config.py")
        return

    builder = FlexibleVectorBuilder()
    success = builder.build_vector_database()

    if success:
        print("\n🚀 Next steps:")
        print("1. Test search: python test_vector_search_flexible.py")
        print("2. Build constitution chat interface")
    else:
        print("\n❌ Build failed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()