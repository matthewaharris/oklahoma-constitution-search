#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) for Oklahoma Constitution
Combines vector search with GPT-4 to answer questions in natural language
"""

import os
from typing import List, Dict
from vector_database_builder import ConstitutionVectorBuilder
import openai

# Import configurations - use environment variables in production
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import OPENAI_API_KEY
else:
    try:
        from pinecone_config import OPENAI_API_KEY
    except ImportError:
        from config_production import OPENAI_API_KEY

class ConstitutionRAG:
    def __init__(self):
        self.builder = ConstitutionVectorBuilder()
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.ready = False

    def initialize(self):
        """Initialize the RAG system"""
        if self.ready:
            return True

        print("Initializing RAG system...")

        # Setup clients
        if not self.builder.setup_clients():
            print("[ERROR] Failed to setup clients")
            return False

        # Connect to index
        try:
            self.builder.index = self.builder.pinecone_client.Index("oklahoma-constitution")
            stats = self.builder.index.describe_index_stats()

            if stats.total_vector_count == 0:
                print("[ERROR] No vectors in index")
                return False

            print(f"[OK] Connected to index with {stats.total_vector_count} vectors")
            self.ready = True
            return True

        except Exception as e:
            print(f"[ERROR] Failed to connect to index: {e}")
            return False

    def search_relevant_sections(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for relevant constitution sections"""
        if not self.ready:
            if not self.initialize():
                return []

        try:
            # Create embedding
            query_embedding = self.builder.create_embeddings([query])
            if not query_embedding:
                return []

            # Search
            search_results = self.builder.index.query(
                vector=query_embedding[0],
                top_k=top_k,
                include_metadata=True
            )

            results = []
            for match in search_results.matches:
                result = {
                    'score': match.score,
                    'cite_id': match.metadata.get('cite_id', 'N/A'),
                    'section_name': match.metadata.get('section_name', 'Untitled'),
                    'article_number': match.metadata.get('article_number', ''),
                    'section_number': match.metadata.get('section_number', ''),
                    'text': match.metadata.get('text', ''),
                }
                results.append(result)

            return results

        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []

    def generate_answer(self, question: str, context_sections: List[Dict], model: str = "gpt-4") -> Dict:
        """Generate a natural language answer using GPT-4"""

        # Build context from relevant sections
        context = ""
        for i, section in enumerate(context_sections, 1):
            article_info = f"Article {section['article_number']}" if section['article_number'] else ""
            section_info = f"Section {section['section_number']}" if section['section_number'] else ""
            location = f"{article_info} {section_info}".strip() or "Unknown location"

            context += f"\n--- Source {i}: {section['section_name']} ({location}) ---\n"
            context += f"{section['text']}\n"

        # Create the prompt
        system_prompt = """You are an expert assistant for the Oklahoma State Constitution.
Your role is to answer questions about the Oklahoma Constitution accurately and clearly.

Guidelines:
1. Base your answer ONLY on the provided constitution text
2. Cite specific sections when answering (e.g., "According to Article II, Section 7...")
3. If the provided text doesn't contain enough information to answer the question, say so
4. Be clear, concise, and accurate
5. Use plain language that citizens can understand
6. If relevant, explain the legal implications or practical meaning"""

        user_prompt = f"""Question: {question}

Relevant sections from the Oklahoma Constitution:
{context}

Please answer the question based on the provided constitutional text. Include citations to specific articles and sections."""

        try:
            # Call GPT-4
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=1000
            )

            answer = response.choices[0].message.content

            return {
                'answer': answer,
                'sources': context_sections,
                'model': model,
                'tokens_used': response.usage.total_tokens
            }

        except Exception as e:
            print(f"[ERROR] GPT generation failed: {e}")
            return {
                'answer': f"Error generating answer: {str(e)}",
                'sources': context_sections,
                'model': model,
                'tokens_used': 0
            }

    def ask_question(self, question: str, num_sources: int = 3, model: str = "gpt-4") -> Dict:
        """
        Main RAG function: Search + Generate Answer

        Args:
            question: User's question about the Oklahoma Constitution
            num_sources: Number of relevant sections to retrieve
            model: OpenAI model to use (gpt-4, gpt-3.5-turbo, etc.)

        Returns:
            Dictionary with answer, sources, and metadata
        """
        if not self.ready:
            if not self.initialize():
                return {
                    'error': 'Failed to initialize RAG system',
                    'answer': None,
                    'sources': []
                }

        print(f"\nQuestion: {question}")
        print(f"Searching for {num_sources} relevant sections...")

        # Step 1: Search for relevant sections
        relevant_sections = self.search_relevant_sections(question, top_k=num_sources)

        if not relevant_sections:
            return {
                'error': 'No relevant sections found',
                'answer': 'I could not find relevant information in the Oklahoma Constitution to answer this question.',
                'sources': []
            }

        print(f"Found {len(relevant_sections)} relevant sections")
        print("Generating answer with GPT-4...")

        # Step 2: Generate answer using GPT-4
        result = self.generate_answer(question, relevant_sections, model)

        print(f"[OK] Answer generated ({result['tokens_used']} tokens used)")

        return result


def test_rag():
    """Test the RAG system with sample questions"""

    rag = ConstitutionRAG()

    if not rag.initialize():
        print("[ERROR] Failed to initialize RAG system")
        return

    # Test questions
    test_questions = [
        "What are the voting rights in Oklahoma?",
        "What does the Oklahoma Constitution say about freedom of speech?",
        "How does Oklahoma handle separation of powers?",
        "What are the requirements for holding public office in Oklahoma?"
    ]

    print("\n" + "=" * 70)
    print("Oklahoma Constitution RAG System - Test")
    print("=" * 70)

    for question in test_questions:
        print("\n" + "-" * 70)
        result = rag.ask_question(question, num_sources=3, model="gpt-4")

        if 'error' not in result:
            print(f"\nQuestion: {question}")
            print(f"\nAnswer:\n{result['answer']}")
            print(f"\nSources used: {len(result['sources'])}")
            print(f"Tokens used: {result['tokens_used']}")
        else:
            print(f"[ERROR] {result['error']}")

        print("-" * 70)
        input("\nPress Enter to continue to next question...")

    print("\n" + "=" * 70)
    print("[SUCCESS] RAG system test completed")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_rag()
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
