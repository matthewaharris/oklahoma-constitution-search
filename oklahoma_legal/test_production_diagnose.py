#!/usr/bin/env python3
"""
Test the /diagnose endpoint on production to see what cite_ids are actually being returned
"""
import requests
import json

# Replace with your actual Render URL
PRODUCTION_URL = "https://oklahoma-constitution-search.onrender.com/"  # UPDATE THIS
LOCAL_URL = "http://localhost:5000"

def test_diagnose(base_url, query="What are child custody laws in Oklahoma?"):
    """Call the /diagnose endpoint and display results"""
    print("=" * 70)
    print(f"Testing: {base_url}/diagnose")
    print("=" * 70)
    print(f"Query: {query}\n")

    try:
        response = requests.post(
            f"{base_url}/diagnose",
            json={"query": query},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            print(f"Environment: {data.get('environment')}")
            print(f"Embedding Model: {data.get('embedding_model')}")
            print(f"Pinecone API Key: {data.get('pinecone_api_key_prefix')}")
            print()

            print("Cite IDs from Pinecone:")
            print("-" * 70)
            cite_ids = data.get('cite_ids_from_pinecone', [])
            print(", ".join(cite_ids))
            print()

            print("Top 10 Pinecone Results:")
            print("-" * 70)
            for i, result in enumerate(data.get('pinecone_results', []), 1):
                cite_id = result.get('cite_id')
                score = result.get('score')
                title = result.get('title_number')
                section = result.get('section_number')
                page_title = result.get('page_title', '')

                print(f"{i}. Cite ID: {cite_id} | Score: {score:.4f}")
                print(f"   Title {title}, Section {section}")
                print(f"   {page_title[:80]}...")
                print()

            print("Supabase Verification (first 5 cite_ids):")
            print("-" * 70)
            for result in data.get('supabase_results', []):
                if 'error' in result:
                    print(f"ERROR: {result['error']}")
                elif 'status' in result:
                    print(f"Cite ID {result['cite_id']}: {result['status']}")
                else:
                    cite_id = result.get('cite_id')
                    title = result.get('title_number')
                    section = result.get('section_number')
                    page_title = result.get('page_title', '')
                    print(f"Cite ID {cite_id}: Title {title}, Section {section}")
                    print(f"  {page_title[:80]}...")

        else:
            print(f"ERROR: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"ERROR calling endpoint: {e}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PRODUCTION DIAGNOSE TEST")
    print("=" * 70)
    print()
    print("This script will help you diagnose the production issue by calling")
    print("the /diagnose endpoint to see exactly what cite_ids Pinecone returns.")
    print()
    print("IMPORTANT: Update PRODUCTION_URL in this script first!")
    print()

    # Test production
    print("\n### TESTING PRODUCTION ###\n")
    test_diagnose(PRODUCTION_URL)

    # Optionally test local for comparison
    test_local = input("\nTest local for comparison? (y/n): ").lower().strip()
    if test_local == 'y':
        print("\n### TESTING LOCAL ###\n")
        test_diagnose(LOCAL_URL)
