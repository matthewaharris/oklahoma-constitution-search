#!/usr/bin/env python3
"""
Quick test of semantic search on Oklahoma Constitution
"""

from typing import List, Dict
from pinecone_config import *
from vector_database_builder import ConstitutionVectorBuilder

class QuickSearchTest:
    def __init__(self):
        self.builder = ConstitutionVectorBuilder()
        self.setup_complete = False

    def setup_search(self):
        """Initialize search capabilities"""
        print("Setting up semantic search...")

        # Setup clients
        if not self.builder.setup_clients():
            return False

        # Connect to existing index
        try:
            self.builder.index = self.builder.pinecone_client.Index(INDEX_NAME)

            # Check if index has data
            stats = self.builder.index.describe_index_stats()
            if stats.total_vector_count == 0:
                print("[ERROR] No vectors found in index.")
                return False

            print(f"[OK] Connected to index with {stats.total_vector_count} vectors")
            self.setup_complete = True
            return True

        except Exception as e:
            print(f"[ERROR] Error connecting to index: {e}")
            return False

    def search_constitution(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform semantic search on the constitution"""

        if not self.setup_complete:
            print("[ERROR] Search not properly initialized")
            return []

        try:
            print(f"\nSearching for: '{query}'")

            # Create embedding for the query
            query_embedding = self.builder.create_embeddings([query])

            if not query_embedding:
                print("[ERROR] Failed to create query embedding")
                return []

            # Search Pinecone
            search_results = self.builder.index.query(
                vector=query_embedding[0],
                top_k=top_k,
                include_metadata=True
            )

            results = []
            for match in search_results.matches:
                result = {
                    'score': match.score,
                    'cite_id': match.metadata.get('cite_id'),
                    'section_name': match.metadata.get('section_name'),
                    'article_number': match.metadata.get('article_number'),
                    'section_number': match.metadata.get('section_number'),
                    'text_preview': match.metadata.get('text', ''),
                    'chunk_info': f"{match.metadata.get('chunk_index', 0) + 1}/{match.metadata.get('total_chunks', 1)}"
                }
                results.append(result)

            return results

        except Exception as e:
            print(f"[ERROR] Search error: {e}")
            return []

    def run_tests(self):
        """Run sample search tests"""

        print("Oklahoma Constitution Semantic Search Test")
        print("=" * 60)

        if not self.setup_search():
            return

        # Test queries
        test_queries = [
            "voting rights and elections",
            "freedom of speech and press",
            "taxation and revenue",
            "separation of powers",
            "due process of law"
        ]

        for query in test_queries:
            results = self.search_constitution(query, top_k=3)

            if results:
                print(f"\nTop {len(results)} results:")
                print("-" * 60)

                for i, result in enumerate(results, 1):
                    score_percentage = result['score'] * 100

                    print(f"{i}. {result['section_name']} (Score: {score_percentage:.1f}%)")

                    if result['article_number']:
                        print(f"   Article {result['article_number']}")
                    if result['section_number']:
                        print(f"   Section {result['section_number']}")

                    print(f"   CiteID: {result['cite_id']}")

                    if result['text_preview']:
                        preview = result['text_preview'][:150] + "..." if len(result['text_preview']) > 150 else result['text_preview']
                        print(f"   Preview: {preview}")

                    print()

            else:
                print("  [ERROR] No results found")

        print("\n" + "=" * 60)
        print("[SUCCESS] Semantic search is working correctly!")
        print("=" * 60)
        print("\nThe vector database is ready for production use.")
        print("You can now build a web interface or chatbot on top of this.")

def main():
    tester = QuickSearchTest()
    tester.run_tests()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
