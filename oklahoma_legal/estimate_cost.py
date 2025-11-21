#!/usr/bin/env python3
"""
Estimate the cost of generating embeddings for Oklahoma statutes/constitution
"""

from supabase_client import StatutesDatabase

def estimate_embedding_cost():
    """Calculate estimated cost for OpenAI embeddings"""

    print("Estimating embedding costs...")
    print("=" * 60)

    db = StatutesDatabase()

    # Get all statute text
    result = db.client.table('statutes').select('cite_id, main_text, title_number').execute()

    total_chars = 0
    constitution_chars = 0
    statute_chars = 0

    for statute in result.data:
        text = statute.get('main_text', '')
        text_len = len(text)
        total_chars += text_len

        if statute.get('title_number') == 'CONST':
            constitution_chars += text_len
        else:
            statute_chars += text_len

    # Token estimation (OpenAI uses ~4 chars per token on average)
    total_tokens = total_chars / 4
    constitution_tokens = constitution_chars / 4
    statute_tokens = statute_chars / 4

    # Cost calculation at $0.02 per million tokens (text-embedding-3-small)
    cost_per_million = 0.02  # Updated: 10x cheaper than ada-002!
    total_cost = (total_tokens / 1_000_000) * cost_per_million
    constitution_cost = (constitution_tokens / 1_000_000) * cost_per_million
    statute_cost = (statute_tokens / 1_000_000) * cost_per_million

    print(f"Total documents: {len(result.data)}")
    print()

    print("CHARACTER COUNTS:")
    print(f"  Constitution: {constitution_chars:,} characters")
    print(f"  Other Statutes: {statute_chars:,} characters")
    print(f"  Total: {total_chars:,} characters")
    print()

    print("ESTIMATED TOKENS (characters / 4):")
    print(f"  Constitution: {constitution_tokens:,.0f} tokens")
    print(f"  Other Statutes: {statute_tokens:,.0f} tokens")
    print(f"  Total: {total_tokens:,.0f} tokens")
    print()

    print("ESTIMATED COSTS (@ $0.02 per million tokens):")
    print(f"  Constitution only: ${constitution_cost:.4f}")
    print(f"  Other Statutes only: ${statute_cost:.4f}")
    print(f"  All documents: ${total_cost:.4f}")
    print()

    print("=" * 60)
    print(f"💰 TOTAL ESTIMATED COST: ${total_cost:.4f}")
    print(f"   (10x cheaper than ada-002! Old cost would have been: ${total_cost*10:.4f})")
    print("=" * 60)
    print()
    print("Notes:")
    print("- This is an ESTIMATE based on ~4 characters per token")
    print("- Actual token count may vary by ±20%")
    print("- OpenAI charges for input tokens to the embedding API")
    print(f"- Model: text-embedding-3-small (UPGRADED)")
    print(f"- Rate: $0.02 per 1 million tokens (10x cheaper than ada-002)")
    print(f"- Quality: Better than ada-002 with improved semantic understanding")

    return {
        'total_chars': total_chars,
        'total_tokens': total_tokens,
        'total_cost': total_cost,
        'constitution_cost': constitution_cost,
        'statute_cost': statute_cost
    }

if __name__ == "__main__":
    try:
        estimate_embedding_cost()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
