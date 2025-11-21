"""
Create final summary of embedding generation
"""
import json
from pinecone import Pinecone
from supabase import create_client, Client
import pinecone_config

# Load credentials
try:
    import config
    SUPABASE_URL = config.SUPABASE_URL
    SUPABASE_KEY = config.SUPABASE_KEY
except ImportError:
    import os
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize clients
pc = Pinecone(api_key=pinecone_config.PINECONE_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("FINAL EMBEDDING GENERATION SUMMARY")
print("=" * 70)

# Check progress file
progress = json.load(open('embedding_progress.json'))
processed_count = len(progress['processed_ids'])
failed_count = len(progress['failed_ids'])
total_cost = progress['total_cost']

print(f"\nProcessing Statistics:")
print(f"  Documents processed: {processed_count:,}")
print(f"  Documents failed: {failed_count}")
print(f"  Total cost: ${total_cost:.2f}")

# Check Supabase total
total_response = supabase.table('statutes').select('*', count='exact').limit(1).execute()
total_in_db = total_response.count

print(f"\nDatabase Status:")
print(f"  Total documents in Supabase: {total_in_db:,}")
print(f"  Documents with embeddings: {processed_count:,}")
print(f"  Completion: {(processed_count / total_in_db * 100):.1f}%")

# Check Pinecone indexes
const_index = pc.Index('oklahoma-constitution')
stat_index = pc.Index('oklahoma-statutes')

const_stats = const_index.describe_index_stats()
stat_stats = stat_index.describe_index_stats()

total_vectors = const_stats.total_vector_count + stat_stats.total_vector_count

print(f"\nPinecone Status:")
print(f"  Constitution vectors: {const_stats.total_vector_count:,}")
print(f"  Statutes vectors: {stat_stats.total_vector_count:,}")
print(f"  Total vectors: {total_vectors:,}")

# Determine status
if processed_count >= total_in_db - 10:  # Allow small margin for errors
    status = "COMPLETE"
else:
    status = f"INCOMPLETE ({processed_count}/{total_in_db})"
    print(f"\nRemaining to process: {total_in_db - processed_count:,} documents")

print(f"\nStatus: {status}")

if failed_count > 0:
    print(f"\nFailed Documents:")
    for failed in progress['failed_ids'][:10]:
        print(f"  - {failed}")
    if failed_count > 10:
        print(f"  ... and {failed_count - 10} more")

print("\n" + "=" * 70)
