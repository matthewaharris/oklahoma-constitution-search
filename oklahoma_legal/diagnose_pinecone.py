#!/usr/bin/env python3
"""
Diagnostic script to verify Pinecone index connectivity and data
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
print("PINECONE DIAGNOSTIC CHECK")
print("=" * 70)

# Check environment
if os.getenv('PRODUCTION'):
    print("\n[INFO] Running in PRODUCTION mode")
elif os.getenv('RENDER'):
    print("\n[INFO] Running on RENDER platform")
else:
    print("\n[INFO] Running in DEVELOPMENT mode")

# Check API key
if not PINECONE_API_KEY:
    print("\n[ERROR] PINECONE_API_KEY not set!")
    exit(1)
else:
    print(f"\n[OK] PINECONE_API_KEY is set (length: {len(PINECONE_API_KEY)})")

# Initialize Pinecone
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    print("[OK] Pinecone client initialized")
except Exception as e:
    print(f"[ERROR] Failed to initialize Pinecone: {e}")
    exit(1)

# Test Constitution index
print("\n" + "-" * 70)
print("Testing Constitution Index")
print("-" * 70)
try:
    const_index = pc.Index("oklahoma-constitution")
    const_stats = const_index.describe_index_stats()
    print(f"[OK] Connected to oklahoma-constitution")
    print(f"     Total vectors: {const_stats.total_vector_count}")
    print(f"     Dimension: {const_stats.dimension if hasattr(const_stats, 'dimension') else 'N/A'}")
    print(f"     Namespaces: {list(const_stats.namespaces.keys()) if const_stats.namespaces else 'default'}")
except Exception as e:
    print(f"[ERROR] Failed to connect to oklahoma-constitution: {e}")

# Test Statutes index
print("\n" + "-" * 70)
print("Testing Statutes Index")
print("-" * 70)
try:
    stat_index = pc.Index("oklahoma-statutes")
    stat_stats = stat_index.describe_index_stats()
    print(f"[OK] Connected to oklahoma-statutes")
    print(f"     Total vectors: {stat_stats.total_vector_count}")
    print(f"     Dimension: {stat_stats.dimension if hasattr(stat_stats, 'dimension') else 'N/A'}")
    print(f"     Namespaces: {list(stat_stats.namespaces.keys()) if stat_stats.namespaces else 'default'}")
except Exception as e:
    print(f"[ERROR] Failed to connect to oklahoma-statutes: {e}")

# Try a simple query test
print("\n" + "-" * 70)
print("Testing Query Capability")
print("-" * 70)

try:
    from vector_database_builder import ConstitutionVectorBuilder
    builder = ConstitutionVectorBuilder()

    if builder.setup_clients():
        print("[OK] Vector builder initialized")

        # Create a test embedding
        test_query = "voting rights"
        print(f"\n[TEST] Creating embedding for: '{test_query}'")
        embedding = builder.create_embeddings([test_query])

        if embedding:
            print(f"[OK] Embedding created (dimension: {len(embedding[0])})")

            # Test query on Constitution index
            print("\n[TEST] Querying Constitution index...")
            const_results = const_index.query(
                vector=embedding[0],
                top_k=3,
                include_metadata=True
            )
            print(f"[OK] Got {len(const_results.matches)} results from Constitution")
            if const_results.matches:
                print(f"     Top result: {const_results.matches[0].metadata.get('page_title', 'N/A')} (score: {const_results.matches[0].score:.4f})")

            # Test query on Statutes index
            print("\n[TEST] Querying Statutes index...")
            stat_results = stat_index.query(
                vector=embedding[0],
                top_k=3,
                include_metadata=True
            )
            print(f"[OK] Got {len(stat_results.matches)} results from Statutes")
            if stat_results.matches:
                print(f"     Top result: {stat_results.matches[0].metadata.get('page_title', 'N/A')} (score: {stat_results.matches[0].score:.4f})")
        else:
            print("[ERROR] Failed to create embedding")
    else:
        print("[ERROR] Failed to initialize vector builder")

except Exception as e:
    print(f"[ERROR] Query test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("DIAGNOSTIC CHECK COMPLETE")
print("=" * 70)
