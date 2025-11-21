"""
Estimate database size requirements for Oklahoma legal documents
"""

# Data from our downloads
TOTAL_FILES = 50_094
HTML_SIZE_MB = 875.8
AVG_FILE_SIZE_KB = 17.9

# Estimates
print("=" * 70)
print("DATABASE SIZE ESTIMATION")
print("=" * 70)

# 1. Raw text storage (after removing HTML tags, typically 30-40% of HTML size)
text_size_mb = HTML_SIZE_MB * 0.35
print(f"\n1. TEXT STORAGE (parsed content):")
print(f"   Estimated size: {text_size_mb:.0f} MB")

# 2. Metadata storage (minimal - citations, titles, etc)
metadata_per_record_kb = 2  # cite_id, title, section, chapter, etc.
metadata_size_mb = (TOTAL_FILES * metadata_per_record_kb) / 1024
print(f"\n2. METADATA:")
print(f"   Estimated size: {metadata_size_mb:.0f} MB")

# 3. Vector embeddings (this is the big one)
EMBEDDING_DIMENSIONS = 1536  # OpenAI text-embedding-3-small or similar
embedding_size_bytes = EMBEDDING_DIMENSIONS * 4  # 4 bytes per float
embedding_size_kb = embedding_size_bytes / 1024
total_embeddings_mb = (TOTAL_FILES * embedding_size_kb) / 1024

print(f"\n3. VECTOR EMBEDDINGS:")
print(f"   Dimensions: {EMBEDDING_DIMENSIONS}")
print(f"   Size per vector: {embedding_size_kb:.1f} KB")
print(f"   Total vectors: {TOTAL_FILES:,}")
print(f"   Total size: {total_embeddings_mb:.0f} MB")

# Total
total_without_vectors = text_size_mb + metadata_size_mb
total_with_vectors = total_without_vectors + total_embeddings_mb

print(f"\n" + "=" * 70)
print("STORAGE OPTIONS")
print("=" * 70)

print(f"\nOPTION 1: Supabase Only (vectors in database)")
print(f"   Total size: {total_with_vectors:.0f} MB")
print(f"   Supabase free tier: 500 MB")
print(f"   X EXCEEDS FREE TIER - Need paid plan ($25/month for Pro)")

print(f"\nOPTION 2: Hybrid (Supabase + Pinecone)")
print(f"   Supabase (text + metadata): {total_without_vectors:.0f} MB")
print(f"   Supabase free tier: 500 MB")
print(f"   OK WITHIN FREE TIER")
print(f"")
print(f"   Pinecone (vectors): {TOTAL_FILES:,} vectors")
print(f"   Pinecone free tier: 100,000 vectors")
print(f"   OK WITHIN FREE TIER")

print(f"\n" + "=" * 70)
print("RECOMMENDATION: OPTION 2 (Hybrid Approach)")
print("=" * 70)
print("""
Why this is better:
  * Both services remain FREE
  * Pinecone is optimized for vector search (faster, better)
  * Supabase handles structured data & metadata (what it's good at)
  * Easy to scale later
  * Better performance for semantic search

Architecture:
  - Supabase: Store statute text, metadata, citations
  - Pinecone: Store vector embeddings for semantic search
  - Application: Query Pinecone for similar docs -> fetch details from Supabase
""")

print("\nAPI Usage Estimates:")
print(f"  Initial embedding creation: ~{TOTAL_FILES:,} API calls")
print(f"  Estimated cost (OpenAI): ${(TOTAL_FILES * 0.00002):.2f}")
print(f"  (Based on text-embedding-3-small pricing)")
