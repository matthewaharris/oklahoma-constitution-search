#!/usr/bin/env python3
"""
Test search on Oklahoma statutes in Pinecone
"""

from vector_database_builder import ConstitutionVectorBuilder

print("Testing Oklahoma Statutes Search")
print("=" * 60)

# Initialize builder
builder = ConstitutionVectorBuilder()

print("Connecting to Pinecone...")
if not builder.setup_clients():
    print("[ERROR] Failed to setup clients")
    exit(1)

# Connect to statutes index
try:
    index = builder.pinecone_client.Index("oklahoma-statutes")
    stats = index.describe_index_stats()

    print(f"[OK] Connected to oklahoma-statutes index")
    print(f"\nIndex Statistics:")
    print(f"  Total vectors: {stats.total_vector_count}")
    print(f"  Dimension: {stats.dimension}")
    print(f"  Index fullness: {stats.index_fullness}")

    if stats.namespaces:
        print(f"\n  Namespaces:")
        for ns_name, ns_stats in stats.namespaces.items():
            print(f"    {ns_name}: {ns_stats.vector_count} vectors")

except Exception as e:
    print(f"[ERROR] Failed to connect: {e}")
    exit(1)

# Test searches
print("\n" + "=" * 60)
print("Testing Sample Searches")
print("=" * 60)

test_queries = [
    "child custody and visitation rights",
    "adoption requirements in Oklahoma",
    "juvenile delinquency procedures",
    "foster care regulations"
]

for i, query in enumerate(test_queries, 1):
    print(f"\n[{i}] Query: \"{query}\"")
    print("-" * 60)

    try:
        # Create embedding
        query_embedding = builder.create_embeddings([query])

        if not query_embedding:
            print("[ERROR] Failed to create embedding")
            continue

        # Search
        results = index.query(
            vector=query_embedding[0],
            top_k=3,
            include_metadata=True
        )

        if results.matches:
            print(f"Found {len(results.matches)} matches:\n")
            for j, match in enumerate(results.matches, 1):
                score = match.score
                cite_id = match.metadata.get('cite_id', 'N/A')
                section_name = match.metadata.get('section_name', 'Untitled')
                text_preview = match.metadata.get('text', '')[:200]

                print(f"{j}. Score: {score:.3f}")
                print(f"   Section: {section_name}")
                print(f"   Cite ID: {cite_id}")
                print(f"   Preview: {text_preview}...")
                print()
        else:
            print("No matches found")

    except Exception as e:
        print(f"[ERROR] Search failed: {e}")

print("=" * 60)
print("[SUCCESS] Search test complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Update web app to search both constitution and statutes")
print("2. Test RAG Q&A with statute context")
print("3. Deploy updated app")
