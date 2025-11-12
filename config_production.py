"""
Production configuration using environment variables
For deployment to Render, Heroku, etc.
"""
import os

# Pinecone Configuration
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east1-gcp')
INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'oklahoma-constitution')
VECTOR_DIMENSION = 1536
METRIC = 'cosine'

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
EMBEDDING_MODEL = 'text-embedding-ada-002'

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Application Settings
BATCH_SIZE = 100
MAX_TEXT_LENGTH = 8000

# Validate required environment variables
def validate_config():
    """Validate that all required environment variables are set"""
    required_vars = {
        'PINECONE_API_KEY': PINECONE_API_KEY,
        'OPENAI_API_KEY': OPENAI_API_KEY,
        'SUPABASE_URL': SUPABASE_URL,
        'SUPABASE_KEY': SUPABASE_KEY
    }

    missing = [key for key, value in required_vars.items() if not value]

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return True

if __name__ == '__main__':
    try:
        validate_config()
        print("[OK] All required environment variables are set")
    except ValueError as e:
        print(f"[ERROR] Configuration validation failed: {e}")
