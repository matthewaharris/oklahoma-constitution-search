#!/usr/bin/env python3
"""
Compare embeddings between local and production Pinecone indexes
This will help identify if embeddings are mismatched
"""
import os
from pinecone import Pinecone
from vector_database_builder import ConstitutionVectorBuilder

# Import configurations
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import PINECONE_API_KEY
else:
    try:
        from pinecone_config import PINECONE_API_KEY
    except ImportError:
        from config_production import PINECONE_API_KEY

print("=" * 70)
print("EMBEDDING COMPARISON - LOCAL VS PRODUCTION")
print("=" * 70)

# Initialize clients
pc = Pinecone(api_key=PINECONE_API_KEY)
builder = ConstitutionVectorBuilder()

if not builder.setup_clients():
    print("[ERROR] Failed to setup clients")
    exit(1)

# Connect to indexes
print("\nConnecting to Pinecone indexes...")
const_index = pc.Index("oklahoma-constitution")
stat_index = pc.Index("oklahoma-statutes")

print("[OK] Connected to both indexes")

# Test query
test_query = "What are child custody laws in Oklahoma?"
print(f"\n{'=' * 70}")
print(f"TEST QUERY: '{test_query}'")
print(f"{'=' * 70}")

# Create embedding
print("\nCreating embedding...")
embedding = builder.create_embeddings([test_query])

if not embedding:
    print("[ERROR] Failed to create embedding")
    exit(1)

print(f"[OK] Embedding created (dimension: {len(embedding[0])})")

# Query both indexes
print("\n" + "-" * 70)
print("CONSTITUTION INDEX RESULTS")
print("-" * 70)

const_results = const_index.query(
    vector=embedding[0],
    top_k=5,
    include_metadata=True
)

if const_results.matches:
    for i, match in enumerate(const_results.matches, 1):
        cite_id = match.metadata.get('cite_id', 'N/A')
        title = match.metadata.get('page_title', 'Untitled')
        score = match.score
        print(f"{i}. Score: {score:.4f} | Cite ID: {cite_id}")
        print(f"   Title: {title}")
        print()
else:
    print("No results found")

print("\n" + "-" * 70)
print("STATUTES INDEX RESULTS")
print("-" * 70)

stat_results = stat_index.query(
    vector=embedding[0],
    top_k=10,  # Get more to see the pattern
    include_metadata=True
)

if stat_results.matches:
    for i, match in enumerate(stat_results.matches, 1):
        cite_id = match.metadata.get('cite_id', 'N/A')
        title = match.metadata.get('page_title', 'Untitled')
        title_num = match.metadata.get('title_number', 'N/A')
        section_num = match.metadata.get('section_number', 'N/A')
        score = match.score

        print(f"{i}. Score: {score:.4f} | Cite ID: {cite_id} | Title {title_num}, §{section_num}")
        print(f"   {title}")
        print()
else:
    print("No results found")

# Now fetch the actual text for top 3 statute results to verify content
print("\n" + "=" * 70)
print("VERIFYING TOP 3 STATUTE RESULTS (fetching from Supabase)")
print("=" * 70)

from supabase import create_client

try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    from config_production import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

for i, match in enumerate(stat_results.matches[:3], 1):
    cite_id = match.metadata.get('cite_id', 'N/A')
    title = match.metadata.get('page_title', 'Untitled')

    print(f"\n{'-' * 70}")
    print(f"Result #{i}: {title} (Cite ID: {cite_id})")
    print(f"{'-' * 70}")

    try:
        result = supabase.table('statutes').select('main_text, title_number, section_number').eq('cite_id', cite_id).limit(1).execute()

        if result.data and len(result.data) > 0:
            text = result.data[0].get('main_text', '')
            title_num = result.data[0].get('title_number', 'N/A')
            section_num = result.data[0].get('section_number', 'N/A')

            print(f"Title: {title_num}, Section: {section_num}")
            print(f"Text preview (first 300 chars):")
            print(f"{text[:300]}...")
        else:
            print("[WARNING] No data found in Supabase for this cite_id")
    except Exception as e:
        print(f"[ERROR] Failed to fetch from Supabase: {e}")

print("\n" + "=" * 70)
print("EXPECTED RESULTS FOR CHILD CUSTODY QUERY")
print("=" * 70)
print("""
Should see statutes from Title 43 (Marriage and Family), such as:
- Title 43, Section 112   - Custody provisions in divorce
- Title 43, Section 112.5 - Custody/guardianship awards
- Title 43, Section 109   - Best interests of child
- Title 43, Section 551-* - Uniform Child Custody Jurisdiction Act

If you're seeing results from other titles (like Title 75, 21, 15),
then the embeddings in the Pinecone index are WRONG or MISMATCHED.
""")

print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)

# Check if we got the right results
correct_results = 0
for match in stat_results.matches[:5]:
    title_num = match.metadata.get('title_number', '')
    if title_num == '43':
        correct_results += 1

if correct_results >= 3:
    print("[✓] EMBEDDINGS ARE CORRECT")
    print(f"    Found {correct_results}/5 results from Title 43 (Marriage and Family)")
    print("    The Pinecone index has the correct embeddings.")
else:
    print("[✗] EMBEDDINGS ARE WRONG OR MISMATCHED")
    print(f"    Only found {correct_results}/5 results from Title 43")
    print("    The Pinecone index appears to have incorrect embeddings.")
    print("\n    POSSIBLE CAUSES:")
    print("    1. Embeddings were generated with a different model")
    print("    2. Embeddings were uploaded to the wrong index")
    print("    3. Embeddings are corrupted or incomplete")
    print("    4. Using a different Pinecone project/environment")

print("\n" + "=" * 70)
