#!/usr/bin/env python3
"""
Test OpenAI API connection and embedding generation
"""

from pinecone_config import OPENAI_API_KEY

def test_openai_connection():
    """Test if OpenAI API key works"""

    print("Testing OpenAI API Connection")
    print("=" * 50)

    if not OPENAI_API_KEY:
        print("[ERROR] No OpenAI API key found in pinecone_config.py")
        return False

    print(f"[OK] API key found: {OPENAI_API_KEY[:20]}...{OPENAI_API_KEY[-10:]}")

    try:
        import openai
        print("[OK] openai package installed")
    except ImportError:
        print("Installing openai package...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openai'])
        import openai
        print("[OK] openai package installed")

    # Test the API connection
    print("\nTesting API connection with sample text...")

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        # Test with a simple embedding request
        test_text = "This is a test of the Oklahoma Constitution embedding system."

        response = client.embeddings.create(
            model="text-embedding-3-small",  # Updated: better quality, 10x cheaper
            input=[test_text]
        )

        embedding = response.data[0].embedding

        print(f"[OK] API connection successful!")
        print(f"[OK] Generated embedding with {len(embedding)} dimensions")
        print(f"[OK] Sample values: {embedding[:5]}")

        # Test with multiple texts
        print("\nTesting batch embedding (3 texts)...")
        test_texts = [
            "Freedom of speech",
            "Right to vote",
            "Due process of law"
        ]

        response = client.embeddings.create(
            model="text-embedding-3-small",  # Updated: better quality, 10x cheaper
            input=test_texts
        )

        print(f"[OK] Batch embedding successful!")
        print(f"[OK] Generated {len(response.data)} embeddings")

        # Calculate approximate cost (text-embedding-3-small: $0.02 per 1M tokens)
        total_chars = sum(len(t) for t in test_texts) + len(test_text)
        estimated_tokens = total_chars / 4
        estimated_cost = (estimated_tokens / 1_000_000) * 0.02  # Updated pricing!

        print(f"\nTest Statistics:")
        print(f"  Characters processed: {total_chars}")
        print(f"  Estimated tokens: {estimated_tokens:.0f}")
        print(f"  Estimated cost: ${estimated_cost:.6f}")

        print("\n" + "=" * 50)
        print("[SUCCESS] OpenAI API is working correctly!")
        print("[SUCCESS] Ready to generate embeddings for Oklahoma Constitution")
        print("=" * 50)

        return True

    except openai.AuthenticationError:
        print("\n[ERROR] Authentication failed!")
        print("   The API key is invalid or expired")
        print("   Please check your OpenAI API key")
        return False

    except openai.RateLimitError:
        print("\n[ERROR] Rate limit exceeded!")
        print("   Your account may have insufficient credits")
        print("   Check your OpenAI account billing")
        return False

    except openai.APIError as e:
        print(f"\n[ERROR] OpenAI API error: {e}")
        return False

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_openai_connection()

        if success:
            print("\nNext steps:")
            print("1. Run vector_database_builder.py to generate embeddings")
            print("2. Or run simple_vector_builder.py for simplified version")
            print("3. Then use test_vector_search.py to test semantic search")
        else:
            print("\nPlease fix the API key issue before proceeding")

    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Error: {e}")
