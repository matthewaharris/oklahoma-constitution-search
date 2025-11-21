#!/usr/bin/env python3
"""
Direct test of Pinecone query to see what cite_ids are returned
"""
import os
from pinecone import Pinecone
from openai import OpenAI

# Import configurations
try:
    from pinecone_config import PINECONE_API_KEY, OPENAI_API_KEY
    print(f"Loaded from pinecone_config")
except ImportError:
    try:
        from config_production import PINECONE_API_KEY, OPENAI_API_KEY
        print(f"Loaded from config_production")
    except Exception as e:
        print(f"Failed to load config: {e}")
        exit(1)

print("=" * 70)
print("DIRECT PINECONE QUERY TEST")
print("=" * 70)
print(f"API Key: {PINECONE_API_KEY[:10]}... (length: {len(PINECONE_API_KEY)})")

# Initialize clients
pc = Pinecone(api_key=PINECONE_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Connect to statutes index
stat_index = pc.Index("oklahoma-statutes")

# Check index stats
stats = stat_index.describe_index_stats()
print(f"\nStatutes Index Stats:")
print(f"  Total vectors: {stats.total_vector_count}")
print(f"  Dimension: {stats.dimension}")

# Create embedding for child custody query
query = "What are child custody laws in Oklahoma?"
print(f"\nQuery: '{query}'")

response = openai_client.embeddings.create(
    input=query,
    model="text-embedding-3-small"
)
embedding = response.data[0].embedding

print(f"Embedding dimension: {len(embedding)}")

# Query Pinecone
print("\nQuerying Pinecone statutes index...")
results = stat_index.query(
    vector=embedding,
    top_k=10,
    include_metadata=True
)

print(f"\nTop 10 cite_ids returned by Pinecone:")
print("-" * 70)

for i, match in enumerate(results.matches, 1):
    cite_id = match.metadata.get('cite_id', 'N/A')
    title = match.metadata.get('page_title', 'Untitled')
    title_num = match.metadata.get('title_number', 'N/A')
    section_num = match.metadata.get('section_number', 'N/A')
    score = match.score

    print(f"{i}. Cite ID: {cite_id} | Score: {score:.4f}")
    print(f"   Title {title_num}, Section {section_num}")
    print(f"   {title[:80]}")
    print()

print("=" * 70)
print("CITE IDS ONLY (for easy comparison):")
print("=" * 70)
cite_ids = [match.metadata.get('cite_id', 'N/A') for match in results.matches]
print(", ".join(cite_ids))
print()
