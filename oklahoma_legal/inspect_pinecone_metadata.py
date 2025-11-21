#!/usr/bin/env python3
"""
Inspect metadata from specific vectors in Pinecone to verify data quality
"""
import os
from pinecone import Pinecone

# Import configurations
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import PINECONE_API_KEY
else:
    try:
        from pinecone_config import PINECONE_API_KEY
    except ImportError:
        from config_production import PINECONE_API_KEY

print("=" * 70)
print("INSPECTING PINECONE METADATA")
print("=" * 70)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Connect to statutes index
stat_index = pc.Index("oklahoma-statutes")

# The cite_ids that production is WRONGLY returning for child custody query
# Based on your production response:
wrong_cite_ids = [
    # These are what production returned (WRONG):
    # "75256.3",  # Cost of copying records (Title 75, Section 256.3)
    # "211981",   # Sound recording forfeiture (Title 21, Section 1981)
    # "15296"     # Borrower repair (Title 15, Section 296)
]

# The cite_ids that should be returned (CORRECT) - from local test
correct_cite_ids = [
    "455331",  # Title 43, Section 112.5 - Custody or Guardianship
    "71829",   # Title 43, Section 112   - Care, Custody, and Support
    "103884"   # Title 43, Section 551-106 - Effect of Child Custody
]

print("\nChecking if CORRECT vectors exist in Pinecone...")
print("-" * 70)

try:
    # Fetch the correct vectors to verify they exist
    result = stat_index.fetch(ids=correct_cite_ids)

    if result.vectors:
        print(f"[OK] Found {len(result.vectors)}/{len(correct_cite_ids)} correct vectors in index")

        for cite_id in correct_cite_ids:
            if cite_id in result.vectors:
                vector = result.vectors[cite_id]
                metadata = vector.metadata if hasattr(vector, 'metadata') else {}
                print(f"\n  Cite ID: {cite_id}")
                print(f"  Title: {metadata.get('page_title', 'N/A')}")
                print(f"  Title Number: {metadata.get('title_number', 'N/A')}")
                print(f"  Section Number: {metadata.get('section_number', 'N/A')}")
                print(f"  Vector exists: YES")
            else:
                print(f"\n  Cite ID: {cite_id} - NOT FOUND IN INDEX!")
    else:
        print("[ERROR] No correct vectors found in index!")

except Exception as e:
    print(f"[ERROR] Failed to fetch vectors: {e}")

# Now let's look at a random sample of vectors to see what's in the index
print("\n" + "=" * 70)
print("SAMPLING RANDOM VECTORS FROM INDEX")
print("=" * 70)

from vector_database_builder import ConstitutionVectorBuilder

builder = ConstitutionVectorBuilder()
if builder.setup_clients():
    # Create embedding for child custody query
    test_query = "child custody laws"
    print(f"\nQuerying with: '{test_query}'")

    embedding = builder.create_embeddings([test_query])

    if embedding:
        # Query to get what Pinecone thinks are the top results
        results = stat_index.query(
            vector=embedding[0],
            top_k=10,
            include_metadata=True
        )

        print(f"\nTop 10 results from Pinecone:")
        print("-" * 70)

        for i, match in enumerate(results.matches, 1):
            cite_id = match.metadata.get('cite_id', 'N/A')
            title = match.metadata.get('page_title', 'Untitled')
            title_num = match.metadata.get('title_number', 'N/A')
            section_num = match.metadata.get('section_number', 'N/A')
            score = match.score

            marker = "✓" if title_num == '43' else "✗"

            print(f"{i}. [{marker}] Score: {score:.4f} | Cite: {cite_id} | Title {title_num}, §{section_num}")
            print(f"   {title[:80]}...")

# Check index statistics
print("\n" + "=" * 70)
print("INDEX STATISTICS")
print("=" * 70)

stats = stat_index.describe_index_stats()
print(f"Total vectors: {stats.total_vector_count}")
print(f"Dimension: {stats.dimension}")
print(f"Namespaces: {list(stats.namespaces.keys()) if stats.namespaces else 'default'}")

if stats.namespaces:
    for ns, ns_stats in stats.namespaces.items():
        ns_name = ns if ns else "(default)"
        print(f"\nNamespace '{ns_name}': {ns_stats.vector_count} vectors")

print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)

print("""
If the top results are showing Title 43 (Marriage and Family) sections,
then the Pinecone index has CORRECT embeddings.

If they're showing other random titles, then either:
1. The embeddings are from old/corrupted data
2. The vectors exist but the embeddings don't match the content
3. There's an issue with the embedding model or process

The API key is the same between local and production, so both should
be accessing the same Pinecone indexes. This suggests the issue might
be with HOW production is querying or processing results, not with
the Pinecone data itself.
""")

print("\n" + "=" * 70)
