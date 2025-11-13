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
    except ImportError:
        from config_production import *

from vector_database_builder import ConstitutionVectorBuilder
from rag_search import ConstitutionRAG

app = Flask(__name__)

# Security: Enable CORS with restrictions
CORS(app, resources={
    r"/search": {"origins": "*"},
    r"/ask": {"origins": "*"},
    r"/health": {"origins": "*"}
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

        # Connect to both indexes
        try:
            # Constitution index
            self.constitution_index = self.builder.pinecone_client.Index("oklahoma-constitution")
            const_stats = self.constitution_index.describe_index_stats()
            print(f"[OK] Connected to Constitution index with {const_stats.total_vector_count} vectors")

            # Statutes index
            self.statutes_index = self.builder.pinecone_client.Index("oklahoma-statutes")
            stat_stats = self.statutes_index.describe_index_stats()
            print(f"[OK] Connected to Statutes index with {stat_stats.total_vector_count} vectors")

            self.ready = True
            return True

        except Exception as e:
            print(f"[ERROR] Failed to connect to indexes: {e}")
            return False

    def search(self, query: str, source: str = 'both', top_k: int = 5) -> List[Dict]:
        """
        Search Oklahoma legal documents

        Args:
            query: Search query
            source: 'constitution', 'statutes', or 'both'
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
                const_results = self.constitution_index.query(
                    vector=query_embedding[0],
                    top_k=top_k,
                    include_metadata=True
                )

                for match in const_results.matches:
                    result = {
                        'score': round(match.score * 100, 1),
                        'source': 'Oklahoma Constitution',
                        'cite_id': match.metadata.get('cite_id', 'N/A'),
                        'section_name': match.metadata.get('section_name', 'Untitled'),
                        'article_number': match.metadata.get('article_number', ''),
                        'section_number': match.metadata.get('section_number', ''),
                        'text': match.metadata.get('text', ''),
                        'type': 'constitution'
                    }
                    results.append(result)

            # Search statutes
            if source in ['statutes', 'both']:
                stat_results = self.statutes_index.query(
                    vector=query_embedding[0],
                    top_k=top_k,
                    include_metadata=True
                )

                for match in stat_results.matches:
                    result = {
                        'score': round(match.score * 100, 1),
                        'source': 'Oklahoma Statutes - Title 10',
                        'cite_id': match.metadata.get('cite_id', 'N/A'),
                        'section_name': match.metadata.get('section_name', 'Untitled'),
                        'title_number': match.metadata.get('title_number', ''),
                        'section_number': match.metadata.get('section_number', ''),
                        'text': match.metadata.get('text', ''),
                        'type': 'statute'
                    }
                    results.append(result)

            # Sort by relevance score
            results.sort(key=lambda x: x['score'], reverse=True)

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
        source = data.get('source', 'both')
        allowed_sources = ['constitution', 'statutes', 'both']
        if source not in allowed_sources:
            source = 'both'

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
