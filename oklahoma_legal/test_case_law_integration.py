#!/usr/bin/env python3
"""
Test Case Law Integration in RAG System
Verifies that case law search is working alongside constitution and statutes
"""

from rag_search import ConstitutionRAG
import sys

def test_case_law_search():
    """Test that case law search is integrated and working"""
    print("="*60)
    print("TESTING CASE LAW INTEGRATION")
    print("="*60)

    # Initialize RAG system
    print("\n1. Initializing RAG system...")
    rag = ConstitutionRAG()
    if not rag.initialize():
        print("[ERROR] Failed to initialize RAG system")
        sys.exit(1)

    # Test 1: Search for relevant sections
    print("\n2. Testing search_relevant_sections()...")
    test_query = "What are the requirements for criminal appeals in Oklahoma?"
    print(f"   Query: '{test_query}'")

    results = rag.search_relevant_sections(test_query, top_k=6)

    # Analyze results
    print(f"\n   Found {len(results)} total results:")
    const_count = sum(1 for r in results if r['document_type'] == 'constitution')
    stat_count = sum(1 for r in results if r['document_type'] == 'statute')
    case_count = sum(1 for r in results if r['document_type'] == 'case_law')

    print(f"   - Constitution: {const_count}")
    print(f"   - Statutes: {stat_count}")
    print(f"   - Case Law: {case_count}")

    # Display top results
    print("\n   Top Results:")
    for i, result in enumerate(results[:6], 1):
        doc_type = result['document_type']
        score = result['score']
        location = result['location']
        section = result['section_name']

        print(f"\n   [{i}] {doc_type.upper()} (score: {score:.3f})")
        print(f"       Location: {location}")
        print(f"       Section: {section[:80]}...")

        # Verify case law has required fields
        if doc_type == 'case_law':
            citation = result.get('citation', '')
            court_type = result.get('court_type', '')
            cite_id = result.get('cite_id', '')
            text = result.get('text', '')

            print(f"       Citation: {citation}")
            print(f"       Court: {court_type}")
            print(f"       CiteID: {cite_id}")
            print(f"       Text length: {len(text)} chars")

            if not text:
                print("       [WARNING] No case text retrieved!")

    # Test 2: Generate answer with GPT-4
    print("\n" + "="*60)
    print("3. Testing answer generation with case law...")
    print("="*60)

    answer_result = rag.ask_question(test_query, num_sources=5, model="gpt-4")

    print("\nQUESTION:", test_query)
    print("\nANSWER:")
    print(answer_result['answer'])

    print("\n\nSOURCES USED:")
    for i, source in enumerate(answer_result['sources'], 1):
        doc_type = source.get('document_type', 'unknown')
        location = source['location']
        section = source['section_name']
        score = source['score']

        print(f"\n[{i}] {doc_type.upper()} (relevance: {score:.3f})")
        print(f"    {location}")
        print(f"    {section[:100]}...")

    # Verify case law appears in sources
    case_sources = [s for s in answer_result['sources'] if s.get('document_type') == 'case_law']
    print(f"\n\n{'='*60}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Total sources: {len(answer_result['sources'])}")
    print(f"Case law sources: {len(case_sources)}")

    if case_sources:
        print("\n✓ SUCCESS: Case law is integrated and appearing in results!")
        for case in case_sources:
            print(f"  - {case['section_name']}")
            print(f"    {case.get('citation', 'No citation')}")
    else:
        print("\n⚠ WARNING: No case law appeared in top results")
        print("  (This may be normal if statutes/constitution are more relevant)")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_case_law_search()
