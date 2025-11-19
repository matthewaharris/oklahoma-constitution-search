#!/usr/bin/env python3
"""
Oklahoma Constitution Search - Web Interface
Flask application for semantic search of the Oklahoma Constitution
"""

from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from typing import List, Dict
import os
import re

# Use environment variables in production, fall back to local config for development
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import *
else:
    try:
        from pinecone_config import *
        from config import SUPABASE_URL, SUPABASE_KEY
    except ImportError:
        from config_production import *

from vector_database_builder import ConstitutionVectorBuilder
from rag_search import ConstitutionRAG
from supabase import create_client

app = Flask(__name__)

# Security: Enable CORS with restrictions
CORS(app, resources={
    r"/search": {"origins": "*"},
    r"/ask": {"origins": "*"},
    r"/health": {"origins": "*"},
    r"/feedback": {"origins": "*"},
    r"/general-feedback": {"origins": "*"}
})

# Security: Rate limiting to prevent abuse
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Security: Input validation
def sanitize_input(text: str, max_length: int = 500) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""

    # Remove any potential script tags or SQL injection attempts
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)

    # Limit length
    text = text[:max_length]

    # Remove excessive whitespace
    text = ' '.join(text.split())

    return text.strip()

# Initialize search system
class SearchSystem:
    def __init__(self):
        self.builder = ConstitutionVectorBuilder()
        self.constitution_index = None
        self.statutes_index = None
        self.case_law_index = None
        self.ag_opinions_index = None
        self.supabase = None
        self.ready = False

    def initialize(self):
        """Initialize the search system"""
        if self.ready:
            return True

        print("Initializing search system...")

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

        # Connect to all Pinecone indexes
        try:
            # Constitution index
            self.constitution_index = self.builder.pinecone_client.Index("oklahoma-constitution")
            const_stats = self.constitution_index.describe_index_stats()
            print(f"[OK] Connected to Constitution index with {const_stats.total_vector_count} vectors")

            # Statutes index
            self.statutes_index = self.builder.pinecone_client.Index("oklahoma-statutes")
            stat_stats = self.statutes_index.describe_index_stats()
            print(f"[OK] Connected to Statutes index with {stat_stats.total_vector_count} vectors")

            # Case law index
            try:
                self.case_law_index = self.builder.pinecone_client.Index("oklahoma-case-law")
                case_stats = self.case_law_index.describe_index_stats()
                print(f"[OK] Connected to Case Law index with {case_stats.total_vector_count} vectors")
            except Exception as e:
                print(f"[WARNING] Case Law index not available: {e}")

            # AG opinions index
            try:
                self.ag_opinions_index = self.builder.pinecone_client.Index("oklahoma-ag-opinions")
                ag_stats = self.ag_opinions_index.describe_index_stats()
                print(f"[OK] Connected to AG Opinions index with {ag_stats.total_vector_count} vectors")
            except Exception as e:
                print(f"[WARNING] AG Opinions index not available: {e}")

            self.ready = True
            return True

        except Exception as e:
            print(f"[ERROR] Failed to connect to indexes: {e}")
            return False

    def get_document_text(self, cite_id: str, max_length: int = 800) -> str:
        """Fetch full document text from Supabase and truncate for display"""
        try:
            result = self.supabase.table('statutes').select('main_text').eq('cite_id', cite_id).limit(1).execute()
            if result.data and len(result.data) > 0:
                text = result.data[0].get('main_text', '')
                # Truncate if too long (for display)
                if len(text) > max_length:
                    # Try to truncate at a sentence boundary
                    truncated = text[:max_length]
                    last_period = truncated.rfind('.')
                    if last_period > max_length * 0.7:  # If we can find a period in the last 30%
                        truncated = truncated[:last_period + 1]
                    return truncated + '...'
                return text
            return ''
        except Exception as e:
            print(f"[ERROR] Failed to fetch text for {cite_id}: {e}")
            return ''

    def get_case_text(self, case_id: int, max_length: int = 800) -> str:
        """Fetch case opinion text from Supabase and truncate for display"""
        try:
            result = self.supabase.table('oklahoma_cases').select('opinion_text').eq('id', case_id).limit(1).execute()
            if result.data and len(result.data) > 0:
                text = result.data[0].get('opinion_text', '')
                # Truncate if too long (for display)
                if len(text) > max_length:
                    truncated = text[:max_length]
                    last_period = truncated.rfind('.')
                    if last_period > max_length * 0.7:
                        truncated = truncated[:last_period + 1]
                    return truncated + '...'
                return text
            return ''
        except Exception as e:
            print(f"[ERROR] Failed to fetch case text for {case_id}: {e}")
            return ''

    def get_ag_opinion_text(self, opinion_id: int, max_length: int = 800) -> str:
        """Fetch AG opinion text from Supabase and truncate for display"""
        try:
            result = self.supabase.table('attorney_general_opinions').select('opinion_text').eq('id', opinion_id).limit(1).execute()
            if result.data and len(result.data) > 0:
                text = result.data[0].get('opinion_text', '')
                # Truncate if too long (for display)
                if len(text) > max_length:
                    truncated = text[:max_length]
                    last_period = truncated.rfind('.')
                    if last_period > max_length * 0.7:
                        truncated = truncated[:last_period + 1]
                    return truncated + '...'
                return text
            return ''
        except Exception as e:
            print(f"[ERROR] Failed to fetch AG opinion text for {opinion_id}: {e}")
            return ''

    def search(self, query: str, source: str = 'all', top_k: int = 5) -> List[Dict]:
        """
        Search Oklahoma legal documents

        Args:
            query: Search query
            source: 'constitution', 'statutes', 'cases', 'ag_opinions', 'both', or 'all'
            top_k: Number of results to return
        """
        if not self.ready:
            if not self.initialize():
                return []

        try:
            # Create embedding
            query_embedding = self.builder.create_embeddings([query])
            if not query_embedding:
                return []

            results = []

            # Search constitution
            if source in ['constitution', 'both']:
                print(f"[DEBUG] Searching Constitution index for: '{query}' (top_k={top_k})")
                const_results = self.constitution_index.query(
                    vector=query_embedding[0],
                    top_k=top_k,
                    include_metadata=True
                )
                print(f"[DEBUG] Constitution search returned {len(const_results.matches)} results")

                for match in const_results.matches:
                    cite_id = match.metadata.get('cite_id', 'N/A')
                    article_num = match.metadata.get('article_number', '')
                    section_num = match.metadata.get('section_number', '')

                    # Build source label
                    source_label = 'Oklahoma Constitution'
                    if article_num:
                        source_label += f' - Article {article_num}'
                        if section_num:
                            source_label += f', Section {section_num}'

                    result = {
                        'score': round(match.score * 100, 1),
                        'source': source_label,
                        'cite_id': cite_id,
                        'section_name': match.metadata.get('page_title', 'Untitled'),
                        'article_number': article_num,
                        'section_number': section_num,
                        'text': self.get_document_text(cite_id),
                        'type': 'constitution'
                    }
                    results.append(result)

            # Search statutes
            if source in ['statutes', 'both']:
                print(f"[DEBUG] Searching Statutes index for: '{query}' (top_k={top_k})")
                stat_results = self.statutes_index.query(
                    vector=query_embedding[0],
                    top_k=top_k,
                    include_metadata=True
                )
                print(f"[DEBUG] Statutes search returned {len(stat_results.matches)} results")

                for match in stat_results.matches:
                    cite_id = match.metadata.get('cite_id', 'N/A')
                    title_num = match.metadata.get('title_number', '')
                    section_num = match.metadata.get('section_number', '')

                    # Build source label
                    source_label = 'Oklahoma Statutes'
                    if title_num:
                        source_label += f' - Title {title_num}'
                        if section_num:
                            source_label += f', Section {section_num}'

                    result = {
                        'score': round(match.score * 100, 1),
                        'source': source_label,
                        'cite_id': cite_id,
                        'section_name': match.metadata.get('page_title', 'Untitled'),
                        'title_number': title_num,
                        'section_number': section_num,
                        'text': self.get_document_text(cite_id),
                        'type': 'statute'
                    }
                    results.append(result)

            # Search case law
            if source in ['cases', 'both', 'all'] and self.case_law_index:
                print(f"[DEBUG] Searching Case Law index for: '{query}' (top_k={top_k})")
                case_results = self.case_law_index.query(
                    vector=query_embedding[0],
                    top_k=top_k,
                    include_metadata=True
                )
                print(f"[DEBUG] Case Law search returned {len(case_results.matches)} results")

                for match in case_results.matches:
                    case_id = int(match.id.replace('case_', ''))
                    citation = match.metadata.get('citation', 'N/A')
                    court_type = match.metadata.get('court_type', '')
                    decision_year = match.metadata.get('decision_year', '')

                    # Build source label
                    source_label = f'{citation}'
                    if court_type:
                        court_name = court_type.replace('_', ' ').title()
                        source_label += f' ({court_name})'

                    result = {
                        'score': round(match.score * 100, 1),
                        'source': source_label,
                        'citation': citation,
                        'case_title': match.metadata.get('case_title', 'Untitled'),
                        'court_type': court_type,
                        'decision_year': decision_year,
                        'decision_date': match.metadata.get('decision_date', ''),
                        'authoring_judge': match.metadata.get('authoring_judge', ''),
                        'oscn_url': match.metadata.get('oscn_url', ''),
                        'text': self.get_case_text(case_id),
                        'type': 'case_law'
                    }
                    results.append(result)

            # Search AG opinions
            if source in ['ag_opinions', 'both', 'all'] and self.ag_opinions_index:
                print(f"[DEBUG] Searching AG Opinions index for: '{query}' (top_k={top_k})")
                ag_results = self.ag_opinions_index.query(
                    vector=query_embedding[0],
                    top_k=top_k,
                    include_metadata=True
                )
                print(f"[DEBUG] AG Opinions search returned {len(ag_results.matches)} results")

                for match in ag_results.matches:
                    ag_id = int(match.id.replace('ag_', ''))
                    citation = match.metadata.get('citation', 'N/A')
                    opinion_year = match.metadata.get('opinion_year', '')

                    # Build source label
                    source_label = f'{citation} (AG Opinion)'

                    result = {
                        'score': round(match.score * 100, 1),
                        'source': source_label,
                        'citation': citation,
                        'opinion_number': match.metadata.get('opinion_number', ''),
                        'opinion_date': match.metadata.get('opinion_date', ''),
                        'opinion_year': opinion_year,
                        'requestor_name': match.metadata.get('requestor_name', ''),
                        'requestor_title': match.metadata.get('requestor_title', ''),
                        'question_presented': match.metadata.get('question_presented', ''),
                        'oscn_url': match.metadata.get('oscn_url', ''),
                        'text': self.get_ag_opinion_text(ag_id),
                        'type': 'ag_opinion'
                    }
                    results.append(result)

            # Sort by relevance score
            results.sort(key=lambda x: x['score'], reverse=True)

            # Log final results summary
            const_count = sum(1 for r in results[:top_k] if r['type'] == 'constitution')
            stat_count = sum(1 for r in results[:top_k] if r['type'] == 'statute')
            case_count = sum(1 for r in results[:top_k] if r['type'] == 'case_law')
            ag_count = sum(1 for r in results[:top_k] if r['type'] == 'ag_opinion')
            print(f"[DEBUG] Returning {len(results[:top_k])} results: {const_count} Constitution, {stat_count} Statutes, {case_count} Case Law, {ag_count} AG Opinions")

            # Return top_k results
            return results[:top_k]

        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []

# Global search system instance
search_system = SearchSystem()

# Global RAG system instance
rag_system = ConstitutionRAG()

# Security: Add security headers to all responses
@app.after_request
def add_security_headers(response):
    """Add security headers to prevent common attacks"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    return response

# Security: Rate limit error handler
@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    return jsonify({
        'error': 'Rate limit exceeded. Please wait a moment and try again.'
    }), 429

@app.route('/')
def index():
    """Homepage with search interface"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
@limiter.limit("30 per minute")  # More restrictive limit for search
def search():
    """Handle search requests"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request'}), 400

        query = sanitize_input(data.get('query', ''), max_length=500)

        if not query:
            return jsonify({'error': 'Please enter a search query'}), 400

        # Validate source parameter
        source = data.get('source', 'all')
        allowed_sources = ['constitution', 'statutes', 'cases', 'ag_opinions', 'both', 'all']
        if source not in allowed_sources:
            source = 'all'

        # Validate top_k parameter
        top_k = data.get('top_k', 5)
        if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
            top_k = 5

        # Perform search
        results = search_system.search(query, source=source, top_k=top_k)

        if not results:
            return jsonify({'error': 'No results found. Please try a different query.'}), 404

        return jsonify({'results': results, 'query': query, 'source': source})

    except Exception as e:
        # Don't expose internal errors to users
        print(f"Search error: {e}")
        return jsonify({'error': 'Search failed. Please try again.'}), 500

@app.route('/ask', methods=['POST'])
@limiter.limit("10 per minute")  # Stricter limit for expensive GPT calls
def ask():
    """Handle RAG question-answering requests"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request'}), 400

        question = sanitize_input(data.get('question', ''), max_length=500)

        if not question:
            return jsonify({'error': 'Please enter a question'}), 400

        # Validate model selection (only allow approved models)
        model = data.get('model', 'gpt-3.5-turbo')
        allowed_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview']
        if model not in allowed_models:
            model = 'gpt-3.5-turbo'

        # Validate num_sources
        num_sources = data.get('num_sources', 3)
        if not isinstance(num_sources, int) or num_sources < 1 or num_sources > 5:
            num_sources = 3

        # Initialize RAG system if needed
        if not rag_system.ready:
            if not rag_system.initialize():
                return jsonify({'error': 'Service temporarily unavailable'}), 503

        # Get answer
        result = rag_system.ask_question(question, num_sources=num_sources, model=model)

        if 'error' in result:
            return jsonify({'error': 'Unable to generate answer. Please try again.'}), 500

        return jsonify({
            'answer': result['answer'],
            'sources': result['sources'],
            'question': question,
            'tokens_used': result['tokens_used'],
            'model': result['model']
        })

    except Exception as e:
        # Don't expose internal errors to users
        print(f"Ask error: {e}")
        return jsonify({'error': 'Unable to process question. Please try again.'}), 500

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    if search_system.ready or search_system.initialize():
        return jsonify({'status': 'healthy', 'ready': True})
    else:
        return jsonify({'status': 'unhealthy', 'ready': False}), 503

@app.route('/diagnose', methods=['POST'])
def diagnose():
    """Diagnostic endpoint to debug production issues - returns raw Pinecone results"""
    try:
        data = request.get_json()
        query = data.get('query', 'What are child custody laws in Oklahoma?')

        # Initialize if needed
        if not search_system.ready:
            if not search_system.initialize():
                return jsonify({'error': 'Service unavailable'}), 503

        # Create embedding for the query
        print(f"[DIAGNOSE] Creating embedding for: {query}")
        query_embedding = search_system.builder.create_embeddings([query])

        if not query_embedding:
            return jsonify({'error': 'Failed to create embedding'}), 500

        # Query Pinecone statutes index directly
        print(f"[DIAGNOSE] Querying Pinecone statutes index...")
        stat_results = search_system.statutes_index.query(
            vector=query_embedding[0],
            top_k=10,
            include_metadata=True
        )

        # Extract cite_ids and metadata
        pinecone_results = []
        cite_ids = []
        for match in stat_results.matches:
            cite_id = match.metadata.get('cite_id', 'N/A')
            cite_ids.append(cite_id)
            pinecone_results.append({
                'cite_id': cite_id,
                'score': float(match.score),
                'title_number': match.metadata.get('title_number', 'N/A'),
                'section_number': match.metadata.get('section_number', 'N/A'),
                'page_title': match.metadata.get('page_title', 'Untitled')[:100]
            })

        print(f"[DIAGNOSE] Pinecone returned cite_ids: {cite_ids}")

        # Try to fetch from Supabase
        supabase_results = []
        try:
            from config_production import SUPABASE_URL, SUPABASE_KEY
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

            for cite_id in cite_ids[:5]:  # Only fetch first 5
                result = supabase.table('statutes').select(
                    'cite_id, page_title, title_number, section_number'
                ).eq('cite_id', cite_id).limit(1).execute()

                if result.data and len(result.data) > 0:
                    supabase_results.append(result.data[0])
                else:
                    supabase_results.append({'cite_id': cite_id, 'status': 'NOT_FOUND'})
        except Exception as e:
            print(f"[DIAGNOSE] Supabase fetch error: {e}")
            supabase_results = [{'error': str(e)}]

        # Return diagnostic information
        return jsonify({
            'query': query,
            'environment': 'production' if os.getenv('PRODUCTION') else 'development',
            'pinecone_api_key_prefix': PINECONE_API_KEY[:15] + '...',
            'pinecone_results': pinecone_results,
            'cite_ids_from_pinecone': cite_ids,
            'supabase_results': supabase_results,
            'embedding_model': EMBEDDING_MODEL
        })

    except Exception as e:
        print(f"[DIAGNOSE] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/feedback', methods=['POST'])
@limiter.limit("10 per minute")
def submit_feedback():
    """Store user feedback for answers and searches"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request'}), 400

        # Validate required fields
        required_fields = ['session_id', 'question', 'answer_type', 'cite_ids', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate rating
        rating = data.get('rating')
        if rating not in [-1, 1]:
            return jsonify({'error': 'Rating must be -1 or 1'}), 400

        # Validate answer_type
        answer_type = data.get('answer_type')
        if answer_type not in ['ask', 'search']:
            return jsonify({'error': 'answer_type must be "ask" or "search"'}), 400

        # Create Supabase client directly (works in both local and production)
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"[FEEDBACK] Failed to connect to Supabase: {e}")
            return jsonify({'error': 'Database connection not available'}), 503

        feedback_data = {
            'session_id': sanitize_input(data.get('session_id'), max_length=100),
            'question': sanitize_input(data.get('question'), max_length=500),
            'answer_type': answer_type,
            'cite_ids': data.get('cite_ids'),  # PostgreSQL array
            'rating': rating,
            'feedback_comment': sanitize_input(data.get('feedback_comment', ''), max_length=500) if data.get('feedback_comment') else None,
            'model_used': data.get('model_used')
        }

        result = supabase.table('user_feedback').insert(feedback_data).execute()

        print(f"[FEEDBACK] Stored feedback: rating={rating}, question={data.get('question')[:50]}...")

        return jsonify({'success': True, 'message': 'Thank you for your feedback!'})

    except Exception as e:
        print(f"[FEEDBACK] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to submit feedback'}), 500

@app.route('/general-feedback', methods=['POST'])
@limiter.limit("10 per minute")
def submit_general_feedback():
    """Store general user feedback and feature requests"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request'}), 400

        # Validate required fields
        required_fields = ['session_id', 'feedback_type', 'subject', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate feedback_type
        feedback_type = data.get('feedback_type')
        valid_types = ['feature_request', 'bug_report', 'general_feedback', 'improvement']
        if feedback_type not in valid_types:
            return jsonify({'error': f'feedback_type must be one of: {", ".join(valid_types)}'}), 400

        # Create Supabase client directly (works in both local and production)
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"[FEEDBACK] Failed to connect to Supabase: {e}")
            return jsonify({'error': 'Database connection not available'}), 503

        feedback_data = {
            'session_id': sanitize_input(data.get('session_id'), max_length=100),
            'feedback_type': feedback_type,
            'subject': sanitize_input(data.get('subject'), max_length=200),
            'message': sanitize_input(data.get('message'), max_length=2000),
            'email': sanitize_input(data.get('email', ''), max_length=100) if data.get('email') else None,
            'user_agent': sanitize_input(data.get('user_agent', ''), max_length=500) if data.get('user_agent') else None
        }

        result = supabase.table('general_feedback').insert(feedback_data).execute()

        print(f"[GENERAL FEEDBACK] Stored: type={feedback_type}, subject={data.get('subject')[:50]}...")

        return jsonify({'success': True, 'message': 'Thank you for your feedback!'})

    except Exception as e:
        print(f"[GENERAL FEEDBACK] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to submit feedback'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Oklahoma Constitution Search - Web Interface")
    print("=" * 60)
    print("\nInitializing search system...")

    if search_system.initialize():
        print("\n[SUCCESS] Search system ready!")
        print("\nStarting web server...")
        print("Open your browser to: http://localhost:5000")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 60)

        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("\n[ERROR] Failed to initialize search system")
        print("Please check your Pinecone and OpenAI API keys")
