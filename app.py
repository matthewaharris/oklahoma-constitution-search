#!/usr/bin/env python3
"""
Oklahoma Constitution Search - Web Interface
Flask application for semantic search of the Oklahoma Constitution
"""

from flask import Flask, render_template, request, jsonify
from typing import List, Dict
import os

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

# Initialize search system
class SearchSystem:
    def __init__(self):
        self.builder = ConstitutionVectorBuilder()
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

        # Connect to index
        try:
            self.builder.index = self.builder.pinecone_client.Index(INDEX_NAME)
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

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search the constitution"""
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
                    'score': round(match.score * 100, 1),
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

# Global search system instance
search_system = SearchSystem()

# Global RAG system instance
rag_system = ConstitutionRAG()

@app.route('/')
def index():
    """Homepage with search interface"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search requests"""
    data = request.get_json()
    query = data.get('query', '').strip()

    if not query:
        return jsonify({'error': 'Please enter a search query'}), 400

    # Get number of results (default 5)
    top_k = data.get('top_k', 5)

    # Perform search
    results = search_system.search(query, top_k)

    if not results:
        return jsonify({'error': 'No results found. Please try a different query.'}), 404

    return jsonify({'results': results, 'query': query})

@app.route('/ask', methods=['POST'])
def ask():
    """Handle RAG question-answering requests"""
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'Please enter a question'}), 400

    # Get model preference (default to gpt-3.5-turbo for cost efficiency)
    model = data.get('model', 'gpt-3.5-turbo')
    num_sources = data.get('num_sources', 3)

    # Initialize RAG system if needed
    if not rag_system.ready:
        if not rag_system.initialize():
            return jsonify({'error': 'RAG system initialization failed'}), 503

    # Get answer
    result = rag_system.ask_question(question, num_sources=num_sources, model=model)

    if 'error' in result:
        return jsonify({'error': result['error']}), 500

    return jsonify({
        'answer': result['answer'],
        'sources': result['sources'],
        'question': question,
        'tokens_used': result['tokens_used'],
        'model': result['model']
    })

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
