#!/usr/bin/env python3
"""
Generate embeddings for Oklahoma case law and AG opinions and upload to Pinecone
"""

import os
import sys
import json
import time
from typing import List, Dict
from supabase import create_client
from pinecone import Pinecone
from openai import OpenAI

# Load credentials - try multiple sources
try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Import Pinecone and OpenAI API keys
try:
    import pinecone_config
    PINECONE_API_KEY = pinecone_config.PINECONE_API_KEY
    OPENAI_API_KEY = pinecone_config.OPENAI_API_KEY
except ImportError:
    try:
        from config_production import PINECONE_API_KEY, OPENAI_API_KEY
    except ImportError:
        PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not all([SUPABASE_URL, SUPABASE_KEY, PINECONE_API_KEY, OPENAI_API_KEY]):
    print("ERROR: Missing required credentials")
    print(f"  SUPABASE_URL: {'SET' if SUPABASE_URL else 'NOT SET'}")
    print(f"  SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'NOT SET'}")
    print(f"  PINECONE_API_KEY: {'SET' if PINECONE_API_KEY else 'NOT SET'}")
    print(f"  OPENAI_API_KEY: {'SET' if OPENAI_API_KEY else 'NOT SET'}")
    sys.exit(1)

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
BATCH_SIZE = 100  # OpenAI embedding batch size
PINECONE_BATCH_SIZE = 100  # Pinecone upsert batch size

# Index names
CASE_LAW_INDEX = "oklahoma-case-law"
AG_OPINIONS_INDEX = "oklahoma-ag-opinions"

# Progress tracking
PROGRESS_FILE = "case_law_embedding_progress.json"


def load_progress():
    """Load progress from previous run"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'cases_processed': [],
        'ag_opinions_processed': [],
        'total_cost': 0.0
    }


def save_progress(progress):
    """Save current progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def create_pinecone_index(index_name: str):
    """Create Pinecone index if it doesn't exist"""
    if index_name not in [idx.name for idx in pc.list_indexes()]:
        print(f"\n[CREATE] Creating Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=EMBEDDING_DIMENSIONS,
            metric='cosine',
            spec={
                'serverless': {
                    'cloud': 'aws',
                    'region': 'us-east-1'
                }
            }
        )
        print(f"[OK] Index created: {index_name}")
        time.sleep(5)  # Wait for index to be ready
    else:
        print(f"[EXISTS] Index already exists: {index_name}")


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using OpenAI"""
    try:
        response = openai_client.embeddings.create(
            input=texts,
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"[ERROR] Failed to generate embeddings: {e}")
        raise


def prepare_case_text(case: Dict) -> str:
    """Prepare case text for embedding"""
    parts = []

    # Add citation and title
    parts.append(f"Citation: {case['citation']}")
    parts.append(f"Title: {case['case_title']}")
    parts.append(f"Court: {case['court_type'].replace('_', ' ').title()}")
    parts.append(f"Decision Date: {case['decision_date']}")

    if case.get('authoring_judge'):
        parts.append(f"Judge: {case['authoring_judge']}")

    # Add opinion text (truncated if too long)
    opinion_text = case['opinion_text']
    if len(opinion_text) > 8000:  # Limit to ~8000 chars
        opinion_text = opinion_text[:8000] + "..."
    parts.append(f"\nOpinion:\n{opinion_text}")

    return "\n".join(parts)


def prepare_ag_opinion_text(opinion: Dict) -> str:
    """Prepare AG opinion text for embedding"""
    parts = []

    # Add citation and basic info
    parts.append(f"Citation: {opinion['citation']}")
    parts.append(f"Opinion Number: {opinion['opinion_number']}")
    parts.append(f"Date: {opinion['opinion_date']}")
    parts.append(f"Requestor: {opinion['requestor_name']}")

    if opinion.get('requestor_title'):
        parts.append(f"Title: {opinion['requestor_title']}")

    if opinion.get('question_presented'):
        parts.append(f"\nQuestion: {opinion['question_presented']}")

    # Add opinion text (truncated if too long)
    opinion_text = opinion['opinion_text']
    if len(opinion_text) > 8000:
        opinion_text = opinion_text[:8000] + "..."
    parts.append(f"\nOpinion:\n{opinion_text}")

    return "\n".join(parts)


def process_cases(progress: Dict):
    """Process and embed all case law"""
    print("\n" + "=" * 60)
    print("PROCESSING CASE LAW")
    print("=" * 60)

    # Fetch all cases
    response = supabase.table('oklahoma_cases').select('*').execute()
    all_cases = response.data
    print(f"\nTotal cases: {len(all_cases)}")

    # Filter out already processed
    processed_ids = set(progress['cases_processed'])
    cases_to_process = [c for c in all_cases if c['id'] not in processed_ids]

    print(f"Already processed: {len(processed_ids)}")
    print(f"Remaining: {len(cases_to_process)}")

    if not cases_to_process:
        print("[SKIP] All cases already processed")
        return

    # Create index
    create_pinecone_index(CASE_LAW_INDEX)
    index = pc.Index(CASE_LAW_INDEX)

    # Process in batches
    total_batches = (len(cases_to_process) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(cases_to_process), BATCH_SIZE):
        batch = cases_to_process[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        print(f"\n[BATCH {batch_num}/{total_batches}] Processing {len(batch)} cases...")

        # Prepare texts
        texts = [prepare_case_text(case) for case in batch]

        # Generate embeddings
        print(f"  Generating embeddings...")
        embeddings = generate_embeddings(texts)

        # Calculate cost (text-embedding-3-small: $0.02 per 1M tokens, ~1 token = 4 chars)
        total_chars = sum(len(text) for text in texts)
        estimated_tokens = total_chars / 4
        cost = (estimated_tokens / 1_000_000) * 0.02
        progress['total_cost'] += cost
        print(f"  Estimated cost: ${cost:.4f} (Total: ${progress['total_cost']:.4f})")

        # Prepare vectors for Pinecone
        vectors = []
        for case, embedding in zip(batch, embeddings):
            vectors.append({
                'id': f"case_{case['id']}",
                'values': embedding,
                'metadata': {
                    'citation': case['citation'],
                    'case_title': case['case_title'][:500],  # Limit metadata size
                    'court_type': case['court_type'],
                    'decision_date': case['decision_date'],
                    'decision_year': case['decision_year'],
                    'authoring_judge': case.get('authoring_judge', '')[:200] if case.get('authoring_judge') else '',
                    'oscn_url': case['oscn_url'],
                    'document_type': 'case_law'
                }
            })

        # Upsert to Pinecone in smaller batches
        for i in range(0, len(vectors), PINECONE_BATCH_SIZE):
            pinecone_batch = vectors[i:i + PINECONE_BATCH_SIZE]
            try:
                index.upsert(vectors=pinecone_batch)
                print(f"  Upserted {len(pinecone_batch)} vectors to Pinecone")
            except Exception as e:
                print(f"  [ERROR] Failed to upsert batch: {e}")
                raise

        # Update progress
        for case in batch:
            progress['cases_processed'].append(case['id'])
        save_progress(progress)

        # Rate limiting
        time.sleep(1)

    print(f"\n[DONE] Processed {len(cases_to_process)} cases")


def process_ag_opinions(progress: Dict):
    """Process and embed all AG opinions"""
    print("\n" + "=" * 60)
    print("PROCESSING AG OPINIONS")
    print("=" * 60)

    # Fetch all AG opinions
    response = supabase.table('attorney_general_opinions').select('*').execute()
    all_opinions = response.data
    print(f"\nTotal AG opinions: {len(all_opinions)}")

    # Filter out already processed
    processed_ids = set(progress['ag_opinions_processed'])
    opinions_to_process = [o for o in all_opinions if o['id'] not in processed_ids]

    print(f"Already processed: {len(processed_ids)}")
    print(f"Remaining: {len(opinions_to_process)}")

    if not opinions_to_process:
        print("[SKIP] All AG opinions already processed")
        return

    # Create index
    create_pinecone_index(AG_OPINIONS_INDEX)
    index = pc.Index(AG_OPINIONS_INDEX)

    # Process in batches
    total_batches = (len(opinions_to_process) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(opinions_to_process), BATCH_SIZE):
        batch = opinions_to_process[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        print(f"\n[BATCH {batch_num}/{total_batches}] Processing {len(batch)} AG opinions...")

        # Prepare texts
        texts = [prepare_ag_opinion_text(opinion) for opinion in batch]

        # Generate embeddings
        print(f"  Generating embeddings...")
        embeddings = generate_embeddings(texts)

        # Calculate cost
        total_chars = sum(len(text) for text in texts)
        estimated_tokens = total_chars / 4
        cost = (estimated_tokens / 1_000_000) * 0.02
        progress['total_cost'] += cost
        print(f"  Estimated cost: ${cost:.4f} (Total: ${progress['total_cost']:.4f})")

        # Prepare vectors for Pinecone
        vectors = []
        for opinion, embedding in zip(batch, embeddings):
            vectors.append({
                'id': f"ag_{opinion['id']}",
                'values': embedding,
                'metadata': {
                    'citation': opinion['citation'],
                    'opinion_number': opinion['opinion_number'],
                    'opinion_date': opinion['opinion_date'],
                    'opinion_year': opinion['opinion_year'],
                    'requestor_name': opinion['requestor_name'][:200],
                    'requestor_title': opinion.get('requestor_title', '')[:100] if opinion.get('requestor_title') else '',
                    'question_presented': opinion.get('question_presented', '')[:500] if opinion.get('question_presented') else '',
                    'oscn_url': opinion['oscn_url'],
                    'document_type': 'ag_opinion'
                }
            })

        # Upsert to Pinecone
        for i in range(0, len(vectors), PINECONE_BATCH_SIZE):
            pinecone_batch = vectors[i:i + PINECONE_BATCH_SIZE]
            try:
                index.upsert(vectors=pinecone_batch)
                print(f"  Upserted {len(pinecone_batch)} vectors to Pinecone")
            except Exception as e:
                print(f"  [ERROR] Failed to upsert batch: {e}")
                raise

        # Update progress
        for opinion in batch:
            progress['ag_opinions_processed'].append(opinion['id'])
        save_progress(progress)

        # Rate limiting
        time.sleep(1)

    print(f"\n[DONE] Processed {len(opinions_to_process)} AG opinions")


def main():
    """Main execution"""
    print("=" * 60)
    print("OKLAHOMA CASE LAW & AG OPINIONS - EMBEDDING GENERATION")
    print("=" * 60)

    # Load progress
    progress = load_progress()

    # Process cases
    process_cases(progress)

    # Process AG opinions
    process_ag_opinions(progress)

    # Final summary
    print("\n" + "=" * 60)
    print("EMBEDDING GENERATION COMPLETE")
    print("=" * 60)
    print(f"Cases processed: {len(progress['cases_processed'])}")
    print(f"AG opinions processed: {len(progress['ag_opinions_processed'])}")
    print(f"Total cost: ${progress['total_cost']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
