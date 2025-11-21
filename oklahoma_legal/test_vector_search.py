#!/usr/bin/env python3
"""
Test semantic search on Oklahoma Constitution vector database
"""

from typing import List, Dict
from pinecone_config import *
from vector_database_builder import ConstitutionVectorBuilder

class ConstitutionSemanticSearch:
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
                print("❌ No vectors found in index. Run vector_database_builder.py first.")
                return False

            print(f"✓ Connected to index with {stats.total_vector_count} vectors")
            self.setup_complete = True
            return True

        except Exception as e:
            print(f"❌ Error connecting to index: {e}")
            return False

    def search_constitution(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform semantic search on the constitution"""

        if not self.setup_complete:
            print("❌ Search not properly initialized")
            return []

        try:
            print(f"Searching for: '{query}'")

            # Create embedding for the query
            query_embedding = self.builder.create_embeddings([query])

            if not query_embedding:
                print("❌ Failed to create query embedding")
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
            print(f"❌ Search error: {e}")
            return []

    def interactive_search(self):
        """Interactive search interface"""

        print("Oklahoma Constitution Semantic Search")
        print("=" * 50)

        if not self.setup_search():
            return

        print("\nEnter search queries (type 'quit' to exit)")
        print("Examples:")
        print("- 'voting rights'")
        print("- 'freedom of speech'")
        print("- 'taxation authority'")
        print("- 'separation of powers'")

        while True:
            query = input("\n🔍 Search: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                break

            if not query:
                continue

            results = self.search_constitution(query)

            if results:
                print(f"\n📋 Found {len(results)} relevant sections:")
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
                        preview = result['text_preview'][:200] + "..." if len(result['text_preview']) > 200 else result['text_preview']
                        print(f"   Preview: {preview}")

                    if result['chunk_info'] != "1/1":
                        print(f"   (Chunk {result['chunk_info']})")

                    print()

            else:
                print("❌ No results found")

        print("Goodbye!")

def main():
    searcher = ConstitutionSemanticSearch()

    print("Choose an option:")
    print("1. Interactive search")
    print("2. Test with sample queries")
    print("3. Exit")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == '1':
        searcher.interactive_search()

    elif choice == '2':
        print("Testing with sample queries...")

        test_queries = [
            "voting rights",
            "freedom of speech",
            "taxation",
            "separation of powers",
            "due process"
        ]

        if searcher.setup_search():
            for query in test_queries:
                print(f"\n🔍 Testing: '{query}'")
                results = searcher.search_constitution(query, top_k=3)

                if results:
                    for result in results[:2]:  # Show top 2
                        print(f"  ✓ {result['section_name']} ({result['score']*100:.1f}%)")
                else:
                    print("  ❌ No results")

    elif choice == '3':
        print("Goodbye!")

    else:
        print("Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()