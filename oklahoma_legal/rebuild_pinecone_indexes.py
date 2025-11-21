#!/usr/bin/env python3
"""
Rebuild Pinecone indexes from scratch with current Supabase data
WARNING: This will delete all existing vectors and recreate them
"""
import os
import json
from pinecone import Pinecone, ServerlessSpec
from vector_database_builder import ConstitutionVectorBuilder
from supabase import create_client

# Import configurations
try:
    from pinecone_config import PINECONE_API_KEY, EMBEDDING_MODEL
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    from config_production import PINECONE_API_KEY, EMBEDDING_MODEL, SUPABASE_URL, SUPABASE_KEY

print("=" * 70)
print("REBUILD PINECONE INDEXES")
print("=" * 70)
print("\nWARNING: This will DELETE all existing vectors and rebuild from scratch!")
print("This is necessary to fix the mismatch between Pinecone cite_ids and Supabase data.")
print("\nCurrent situation:")
print("  - Pinecone has old cite_ids that don't match current Supabase data")
print("  - Queries return wrong results because cite_ids point to different documents")
print("\n" + "=" * 70)

response = input("\nAre you sure you want to proceed? (type 'YES' to continue): ")

if response != 'YES':
    print("\nAborted. No changes made.")
    exit(0)

print("\n" + "=" * 70)
print("STEP 1: Initialize clients")
print("=" * 70)

pc = Pinecone(api_key=PINECONE_API_KEY)
builder = ConstitutionVectorBuilder()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if not builder.setup_clients():
    print("[ERROR] Failed to setup clients")
    exit(1)

print("[OK] Clients initialized")

# Check current index stats before deletion
print("\n" + "=" * 70)
print("STEP 2: Check current indexes")
print("=" * 70)

try:
    const_index = pc.Index("oklahoma-constitution")
    stat_index = pc.Index("oklahoma-statutes")

    const_stats = const_index.describe_index_stats()
    stat_stats = stat_index.describe_index_stats()

    print(f"Current Constitution vectors: {const_stats.total_vector_count}")
    print(f"Current Statutes vectors: {stat_stats.total_vector_count}")

except Exception as e:
    print(f"[WARNING] Could not get current stats: {e}")

print("\n" + "=" * 70)
print("STEP 3: Delete all vectors from existing indexes")
print("=" * 70)

# Instead of deleting indexes, delete all vectors
# This is safer and faster
for index_name in ["oklahoma-constitution", "oklahoma-statutes"]:
    try:
        print(f"Deleting all vectors from: {index_name}...")
        index = pc.Index(index_name)
        index.delete(delete_all=True)
        print(f"[OK] Deleted all vectors from {index_name}")

        # Wait for deletion to complete
        import time
        time.sleep(3)
    except Exception as e:
        print(f"[ERROR] Failed to delete vectors from {index_name}: {e}")

print("\n" + "=" * 70)
print("STEP 4: Verify indexes are empty")
print("=" * 70)

const_index = pc.Index("oklahoma-constitution")
stat_index = pc.Index("oklahoma-statutes")

import time
time.sleep(5)  # Wait for deletion to complete

const_stats = const_index.describe_index_stats()
stat_stats = stat_index.describe_index_stats()

print(f"Constitution vectors: {const_stats.total_vector_count} (should be 0)")
print(f"Statutes vectors: {stat_stats.total_vector_count} (should be 0)")

if const_stats.total_vector_count > 0 or stat_stats.total_vector_count > 0:
    print("\n[WARNING] Some vectors still remain. Waiting longer for deletion...")
    time.sleep(10)
    const_stats = const_index.describe_index_stats()
    stat_stats = stat_index.describe_index_stats()
    print(f"Constitution vectors: {const_stats.total_vector_count}")
    print(f"Statutes vectors: {stat_stats.total_vector_count}")

print("[OK] Indexes are ready for new data")

print("\n" + "=" * 70)
print("STEP 5: Re-upload embeddings")
print("=" * 70)

print("\nNow you need to run the embedding generation script:")
print("\n  python generate_and_upload_embeddings.py")
print("\nThis will:")
print("  1. Read all documents from Supabase")
print("  2. Generate embeddings with text-embedding-3-small")
print("  3. Upload to the correct Pinecone index based on document_type")
print("  4. Use the CURRENT cite_ids from Supabase")

print("\n" + "=" * 70)
print("INDEX REBUILD COMPLETE")
print("=" * 70)

print("\nNext steps:")
print("1. Run: python generate_and_upload_embeddings.py")
print("2. Wait for all 50,091 embeddings to be generated and uploaded")
print("3. Test the app locally to verify correct results")
print("4. Deploy to production (Render will use the updated indexes)")

print("\n" + "=" * 70)
