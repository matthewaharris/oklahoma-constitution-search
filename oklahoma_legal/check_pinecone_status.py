"""
Check Pinecone index status
"""
from pinecone import Pinecone
import pinecone_config

# Initialize Pinecone
pc = Pinecone(api_key=pinecone_config.PINECONE_API_KEY)

print("=" * 70)
print("PINECONE INDEX STATUS")
print("=" * 70)

# List all indexes
indexes = pc.list_indexes()
print(f"\nAvailable indexes:")
for idx in indexes:
    print(f"  - {idx['name']}")

# Check both indexes
for index_name in ['oklahoma-constitution', 'oklahoma-statutes']:
    print(f"\n{'=' * 70}")
    print(f"Index: {index_name}")
    print('=' * 70)

    try:
        # Get index stats
        index = pc.Index(index_name)
        stats = index.describe_index_stats()

        print(f"\nTotal vectors: {stats.total_vector_count:,}")
        print(f"Dimension: {stats.dimension}")

        if stats.namespaces:
            print(f"\nNamespaces:")
            for ns_name, ns_stats in stats.namespaces.items():
                print(f"  {ns_name}: {ns_stats.vector_count:,} vectors")
        else:
            print(f"\nNo namespaces found - index is empty")

    except Exception as e:
        print(f"Error accessing index: {e}")

print("\n" + "=" * 70)
