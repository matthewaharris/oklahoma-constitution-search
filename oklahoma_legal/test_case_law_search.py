#!/usr/bin/env python3
"""
Test case law and AG opinion search
"""

import requests
import json

# Test endpoint
url = "http://localhost:5000/search"

# Test queries
test_queries = [
    {"query": "criminal procedure", "source": "all", "description": "Search all sources for criminal procedure"},
    {"query": "state rights and powers", "source": "cases", "description": "Search only case law"},
    {"query": "legislative authority", "source": "ag_opinions", "description": "Search only AG opinions"},
]

print("=" * 60)
print("TESTING CASE LAW & AG OPINION SEARCH")
print("=" * 60)

for test in test_queries:
    print(f"\n{test['description']}")
    print(f"Query: '{test['query']}' | Source: {test['source']}")
    print("-" * 60)

    try:
        response = requests.post(url, json={
            "query": test['query'],
            "source": test['source'],
            "top_k": 3
        })

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            print(f"Found {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. [{result['type'].upper()}] {result['source']}")
                print(f"   Score: {result['score']}%")

                # Show type-specific fields
                if result['type'] == 'case_law':
                    print(f"   Case: {result.get('case_title', 'N/A')}")
                    print(f"   Judge: {result.get('authoring_judge', 'N/A')}")
                elif result['type'] == 'ag_opinion':
                    print(f"   Requestor: {result.get('requestor_name', 'N/A')}")
                    print(f"   Question: {result.get('question_presented', 'N/A')[:80]}...")

                print(f"   URL: {result.get('oscn_url', 'N/A')}")
                print()

        else:
            print(f"ERROR: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"ERROR: {e}")

print("=" * 60)
