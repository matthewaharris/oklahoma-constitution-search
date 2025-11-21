#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) for Oklahoma Constitution
Combines vector search with GPT-4 to answer questions in natural language
"""

import os
from typing import List, Dict
from vector_database_builder import ConstitutionVectorBuilder
from supabase import create_client
import openai

# Import configurations - use environment variables in production
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY
else:
    try:
        from pinecone_config import OPENAI_API_KEY
        from config import SUPABASE_URL, SUPABASE_KEY
    except ImportError:
        from config_production import OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY

class ConstitutionRAG:
    def __init__(self):
        self.builder = ConstitutionVectorBuilder()
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.supabase = None
        self.constitution_index = None
        self.statutes_index = None
        self.case_law_index = None
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

        # Connect to Supabase
        try:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("[OK] Connected to Supabase")
        except Exception as e:
            print(f"[ERROR] Failed to connect to Supabase: {e}")
            return False

        # Connect to all indexes
        try:
            # Constitution index
            self.constitution_index = self.builder.pinecone_client.Index("oklahoma-constitution")
            const_stats = self.constitution_index.describe_index_stats()
            print(f"[OK] Connected to Constitution index with {const_stats.total_vector_count} vectors")

            # Statutes index
            self.statutes_index = self.builder.pinecone_client.Index("oklahoma-statutes")
            stat_stats = self.statutes_index.describe_index_stats()
            print(f"[OK] Connected to Statutes index with {stat_stats.total_vector_count} vectors")

            # Case Law index
            self.case_law_index = self.builder.pinecone_client.Index("oklahoma-case-law")
            case_stats = self.case_law_index.describe_index_stats()
            print(f"[OK] Connected to Case Law index with {case_stats.total_vector_count} vectors")

            self.ready = True
            return True

        except Exception as e:
            print(f"[ERROR] Failed to connect to indexes: {e}")
            return False

    def get_document_text(self, cite_id: str, max_length: int = 1500) -> str:
        """Fetch document text from Supabase and truncate for context window"""
        try:
            result = self.supabase.table('statutes').select('main_text').eq('cite_id', cite_id).limit(1).execute()
            if result.data and len(result.data) > 0:
                text = result.data[0].get('main_text', '')
                # Truncate if too long to fit in context window
                if len(text) > max_length:
                    # Try to truncate at a sentence boundary
                    truncated = text[:max_length]
                    last_period = truncated.rfind('.')
                    if last_period > max_length * 0.7:  # If we can find a period in the last 30%
                        truncated = truncated[:last_period + 1]
                    return truncated + "\n[Text truncated for length...]"
                return text
            return ''
        except Exception as e:
            print(f"[ERROR] Failed to fetch text for {cite_id}: {e}")
            return ''

    def get_case_text(self, cite_id: str, max_length: int = 2000) -> str:
        """Fetch case law text from Supabase and truncate for context window"""
        try:
            result = self.supabase.table('oklahoma_cases').select('opinion_text, syllabus').eq('cite_id', cite_id).limit(1).execute()
            if result.data and len(result.data) > 0:
                # Combine syllabus and opinion text
                syllabus = result.data[0].get('syllabus', '')
                opinion = result.data[0].get('opinion_text', '')

                # Syllabus first (summary), then opinion
                text = ""
                if syllabus:
                    text += "SYLLABUS:\n" + syllabus + "\n\n"
                if opinion:
                    text += "OPINION:\n" + opinion

                # Truncate if too long
                if len(text) > max_length:
                    truncated = text[:max_length]
                    last_period = truncated.rfind('.')
                    if last_period > max_length * 0.7:
                        truncated = truncated[:last_period + 1]
                    return truncated + "\n[Text truncated for length...]"
                return text
            return ''
        except Exception as e:
            print(f"[ERROR] Failed to fetch case text for {cite_id}: {e}")
            return ''

    def search_relevant_sections(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for relevant sections from both Constitution and Statutes"""
        if not self.ready:
            if not self.initialize():
                return []

        try:
            # Create embedding
            query_embedding = self.builder.create_embeddings([query])
            if not query_embedding:
                return []

            results = []

            # Search Constitution index
            print(f"[DEBUG] RAG: Searching Constitution index for: '{query}' (top_k={top_k})")
            const_results = self.constitution_index.query(
                vector=query_embedding[0],
                top_k=top_k,
                include_metadata=True
            )
            print(f"[DEBUG] RAG: Constitution search returned {len(const_results.matches)} results")

            for match in const_results.matches:
                cite_id = match.metadata.get('cite_id', 'N/A')
                article_num = match.metadata.get('article_number', '')
                section_num = match.metadata.get('section_number', '')

                # Build location label
                location = "Oklahoma Constitution"
                if article_num:
                    location += f" - Article {article_num}"
                    if section_num:
                        location += f", Section {section_num}"

                result = {
                    'score': match.score,
                    'cite_id': cite_id,
                    'section_name': match.metadata.get('page_title', 'Untitled'),
                    'location': location,
                    'document_type': 'constitution',
                    'article_number': article_num,
                    'section_number': section_num,
                    'text': self.get_document_text(cite_id),
                }
                results.append(result)

            # Search Statutes index
            print(f"[DEBUG] RAG: Searching Statutes index for: '{query}' (top_k={top_k})")
            stat_results = self.statutes_index.query(
                vector=query_embedding[0],
                top_k=top_k,
                include_metadata=True
            )
            print(f"[DEBUG] RAG: Statutes search returned {len(stat_results.matches)} results")

            for match in stat_results.matches:
                cite_id = match.metadata.get('cite_id', 'N/A')
                title_num = match.metadata.get('title_number', '')
                section_num = match.metadata.get('section_number', '')

                # Build location label
                location = "Oklahoma Statutes"
                if title_num:
                    location += f" - Title {title_num}"
                    if section_num:
                        location += f", Section {section_num}"

                result = {
                    'score': match.score,
                    'cite_id': cite_id,
                    'section_name': match.metadata.get('page_title', 'Untitled'),
                    'location': location,
                    'document_type': 'statute',
                    'title_number': title_num,
                    'section_number': section_num,
                    'text': self.get_document_text(cite_id),
                }
                results.append(result)

            # Search Case Law index
            print(f"[DEBUG] RAG: Searching Case Law index for: '{query}' (top_k={top_k})")
            case_results = self.case_law_index.query(
                vector=query_embedding[0],
                top_k=top_k,
                include_metadata=True
            )
            print(f"[DEBUG] RAG: Case Law search returned {len(case_results.matches)} results")

            for match in case_results.matches:
                cite_id = match.metadata.get('cite_id', 'N/A')
                citation = match.metadata.get('citation', '')
                case_title = match.metadata.get('case_title', 'Untitled Case')
                court_type = match.metadata.get('court_type', 'unknown')

                # Build location label
                court_name_map = {
                    'supreme_court': 'Oklahoma Supreme Court',
                    'criminal_appeals': 'Oklahoma Court of Criminal Appeals',
                    'civil_appeals': 'Oklahoma Court of Civil Appeals'
                }
                location = court_name_map.get(court_type, 'Oklahoma Court')
                if citation:
                    location += f" - {citation}"

                result = {
                    'score': match.score,
                    'cite_id': cite_id,
                    'section_name': case_title,
                    'location': location,
                    'document_type': 'case_law',
                    'citation': citation,
                    'court_type': court_type,
                    'text': self.get_case_text(cite_id),
                }
                results.append(result)

            # Sort by relevance score and return top_k
            results.sort(key=lambda x: x['score'], reverse=True)

            # Log final results summary
            const_count = sum(1 for r in results[:top_k] if r['document_type'] == 'constitution')
            stat_count = sum(1 for r in results[:top_k] if r['document_type'] == 'statute')
            case_count = sum(1 for r in results[:top_k] if r['document_type'] == 'case_law')
            print(f"[DEBUG] RAG: Returning {len(results[:top_k])} results: {const_count} Constitution, {stat_count} Statutes, {case_count} Case Law")

            return results[:top_k]

        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []

    def generate_answer(self, question: str, context_sections: List[Dict], model: str = "gpt-4", conversation_history: List[Dict] = None) -> Dict:
        """Generate a natural language answer using GPT-4 with conversation history"""

        # Build context from relevant sections
        context = ""
        for i, section in enumerate(context_sections, 1):
            context += f"\n--- Source {i}: {section['section_name']} ({section['location']}) ---\n"
            context += f"{section['text']}\n"

        # Check relevance scores - if highest score is below 0.5, the question might not be about OK law
        max_score = max([s['score'] for s in context_sections]) if context_sections else 0
        is_likely_ok_law_question = max_score > 0.5

        # Create the prompt - different approach based on relevance
        if is_likely_ok_law_question:
            # High relevance - stick to the legal documents
            system_prompt = """You are an expert assistant for Oklahoma law, including the Oklahoma Constitution, Oklahoma Statutes, and Oklahoma Case Law (court opinions).
Your role is to answer questions about Oklahoma law accurately and clearly.

Guidelines:
1. Base your answer PRIMARILY on the provided legal text
2. Cite specific sources when answering (e.g., "According to Oklahoma Constitution Article II, Section 7...", "According to Oklahoma Statutes Title 43, Section 109...", or "In the case of Smith v. State...")
3. If the provided text doesn't contain enough information to answer the question fully, you may supplement with general legal knowledge, but clearly distinguish between what's in the source documents and general information
4. Be clear, concise, and accurate - aim for 2-3 paragraphs maximum
5. Use plain language that citizens can understand
6. If relevant, explain the legal implications or practical meaning
7. Distinguish between constitutional provisions, statutory law, and case law when relevant
8. When citing cases, include the court name and citation if provided
9. Provide a focused summary rather than exhaustive detail
10. If this is a follow-up question, use the conversation history to provide context-aware answers"""

            user_prompt = f"""Question: {question}

Relevant sections from Oklahoma law (Constitution, Statutes, and Case Law):
{context}

Please answer the question based on the provided legal text. Include citations to specific sources."""

        else:
            # Low relevance - question might not be about OK law, allow general knowledge
            system_prompt = """You are a helpful AI assistant with knowledge of Oklahoma law and general information.

When answering questions:
1. If the question is about Oklahoma law and relevant legal text is provided, base your answer on that text and cite sources
2. If the question is NOT about Oklahoma law (e.g., general knowledge questions), you may answer using your general knowledge
3. If legal sources are provided but not very relevant to the question, acknowledge this and provide a helpful answer anyway
4. Be clear, concise, and accurate
5. Use plain language that anyone can understand
6. If this is a follow-up question, use the conversation history to provide context-aware answers"""

            user_prompt = f"""Question: {question}

Note: I searched Oklahoma legal documents but found limited relevance (best match score: {max_score:.2f}).
Here are the closest matches found:
{context}

Please answer the question. If it's about Oklahoma law, use the sources above. If it's a general question, you may use your general knowledge to help the user."""

        try:
            # Build messages array with conversation history
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history if available (limit to last 10 messages to avoid token limits)
            if conversation_history:
                # Only include the last 10 messages to keep context manageable
                recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
                messages.extend(recent_history)
                print(f"[DEBUG] Including {len(recent_history)} messages from conversation history")

            # Add the current question
            messages.append({"role": "user", "content": user_prompt})

            # Call GPT-4 with shorter response limit
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=500  # Reduced from 1000 to ensure concise responses
            )

            answer = response.choices[0].message.content

            return {
                'answer': answer,
                'sources': context_sections,
                'model': model,
                'tokens_used': response.usage.total_tokens
            }

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] GPT generation failed: {error_msg}")

            # Handle context length errors specifically
            if 'context_length_exceeded' in error_msg or 'maximum context length' in error_msg:
                return {
                    'error': 'Context too long',
                    'answer': "The retrieved legal text is too long to process. Please try asking a more specific question or search for specific statutes instead.",
                    'sources': context_sections,
                    'model': model,
                    'tokens_used': 0
                }

            return {
                'error': 'Generation failed',
                'answer': f"Unable to generate answer: {error_msg}",
                'sources': context_sections,
                'model': model,
                'tokens_used': 0
            }

    def ask_question(self, question: str, num_sources: int = 3, model: str = "gpt-4", conversation_history: List[Dict] = None) -> Dict:
        """
        Main RAG function: Search + Generate Answer

        Args:
            question: User's question about Oklahoma law (Constitution and Statutes)
            num_sources: Number of relevant sections to retrieve
            model: OpenAI model to use (gpt-4, gpt-3.5-turbo, etc.)
            conversation_history: Optional conversation history for context

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
                'answer': 'I could not find relevant information in Oklahoma law to answer this question.',
                'sources': []
            }

        print(f"Found {len(relevant_sections)} relevant sections")
        print("Generating answer with GPT-4...")

        # Step 2: Generate answer using GPT-4 with conversation history
        result = self.generate_answer(question, relevant_sections, model, conversation_history)

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
