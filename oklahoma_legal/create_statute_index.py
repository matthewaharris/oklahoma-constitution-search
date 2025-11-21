#!/usr/bin/env python3
"""
Create Pinecone index for Oklahoma statutes
"""

from vector_database_builder import ConstitutionVectorBuilder
from pinecone import ServerlessSpec

print("Creating Oklahoma Statutes Pinecone Index")
print("=" * 60)

builder = ConstitutionVectorBuilder()

# Setup clients
print("Connecting to Pinecone...")
if not builder.setup_clients():
    print("[ERROR] Failed to setup clients")
    exit(1)

print("[OK] Connected to Pinecone")

# Create index
index_name = "oklahoma-statutes"

# Check if already exists
existing_indexes = [index.name for index in builder.pinecone_client.list_indexes()]

if index_name in existing_indexes:
    print(f"[INFO] Index '{index_name}' already exists")
    response = input("Delete and recreate? (yes/no): ")
    if response.lower() == 'yes':
        print(f"Deleting existing index '{index_name}'...")
        builder.pinecone_client.delete_index(index_name)
        print("[OK] Deleted")
    else:
        print("Using existing index")
        exit(0)

print(f"\nCreating new index: '{index_name}'")
print("Configuration:")
print("  - Dimension: 1536 (OpenAI ada-002)")
print("  - Metric: cosine")
print("  - Cloud: AWS")
print("  - Region: us-east-1")

try:
    builder.pinecone_client.create_index(
        name=index_name,
        dimension=1536,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

    print(f"\n[SUCCESS] Index '{index_name}' created!")
    print("\nYou can now run html_processor.py to upload statutes")
    print("=" * 60)

except Exception as e:
    print(f"[ERROR] Failed to create index: {e}")
    exit(1)
