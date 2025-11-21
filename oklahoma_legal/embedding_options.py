#!/usr/bin/env python3
"""
Multiple embedding options for Oklahoma Constitution vector database
Supports OpenAI, Anthropic, HuggingFace (free), and local models
"""

import json
import time
from typing import List, Dict, Any
import requests

class EmbeddingProvider:
    """Base class for embedding providers"""

    def __init__(self):
        self.dimension = None
        self.model_name = None

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def get_dimension(self) -> int:
        return self.dimension

class OpenAIEmbeddings(EmbeddingProvider):
    """OpenAI embeddings provider"""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.model_name = "text-embedding-3-small"  # Updated: 10x cheaper, better quality
        self.dimension = 1536

        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("Install with: pip install openai")

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            return []

class AnthropicEmbeddings(EmbeddingProvider):
    """Anthropic embeddings provider (if available)"""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.dimension = 1536  # Check Anthropic docs for actual dimension

        # Note: As of my knowledge cutoff, Anthropic doesn't offer embedding endpoints
        # This is a placeholder for when/if they do
        print("⚠️ Anthropic embeddings not yet available")
        print("   Anthropic focuses on conversational AI, not embeddings")
        print("   Consider using HuggingFace or OpenAI alternatives")

class HuggingFaceEmbeddings(EmbeddingProvider):
    """Free HuggingFace embeddings using sentence-transformers"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__()
        self.model_name = model_name
        self.dimension = 384  # Default for all-MiniLM-L6-v2

        try:
            from sentence_transformers import SentenceTransformer
            print(f"Loading HuggingFace model: {model_name}")
            self.model = SentenceTransformer(model_name)

            # Get actual dimension
            self.dimension = self.model.get_sentence_embedding_dimension()
            print(f"✓ Model loaded, dimension: {self.dimension}")

        except ImportError:
            print("Installing sentence-transformers...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'sentence-transformers'])
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = self.model.encode(texts)
            return [embedding.tolist() for embedding in embeddings]
        except Exception as e:
            print(f"HuggingFace embedding error: {e}")
            return []

class CohereEmbeddings(EmbeddingProvider):
    """Cohere embeddings provider (good OpenAI alternative)"""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.model_name = "embed-english-v3.0"
        self.dimension = 1024  # Cohere dimension

        try:
            import cohere
            self.client = cohere.Client(api_key)
        except ImportError:
            print("Installing cohere...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'cohere'])
            import cohere
            self.client = cohere.Client(api_key)

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embed(
                texts=texts,
                model=self.model_name,
                input_type="search_document"
            )
            return response.embeddings
        except Exception as e:
            print(f"Cohere embedding error: {e}")
            return []

class EmbeddingFactory:
    """Factory to create embedding providers"""

    @staticmethod
    def create_provider(provider_type: str, **kwargs) -> EmbeddingProvider:
        """Create an embedding provider"""

        if provider_type == "openai":
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("OpenAI requires API key")
            return OpenAIEmbeddings(api_key)

        elif provider_type == "huggingface":
            model_name = kwargs.get("model_name", "all-MiniLM-L6-v2")
            return HuggingFaceEmbeddings(model_name)

        elif provider_type == "cohere":
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("Cohere requires API key")
            return CohereEmbeddings(api_key)

        elif provider_type == "anthropic":
            return AnthropicEmbeddings(kwargs.get("api_key", ""))

        else:
            raise ValueError(f"Unknown provider: {provider_type}")

    @staticmethod
    def list_providers():
        """List available embedding providers"""
        providers = {
            "huggingface": {
                "name": "HuggingFace (FREE)",
                "description": "Free, local sentence-transformers models",
                "requires_api_key": False,
                "dimension": 384,
                "pros": ["Completely free", "Runs locally", "No API limits", "Privacy-friendly"],
                "cons": ["Larger model size", "Slightly lower quality than OpenAI"]
            },
            "openai": {
                "name": "OpenAI",
                "description": "High-quality embeddings from OpenAI",
                "requires_api_key": True,
                "dimension": 1536,
                "pros": ["High quality", "Fast API", "Well-tested"],
                "cons": ["Requires payment", "API rate limits"]
            },
            "cohere": {
                "name": "Cohere",
                "description": "Alternative to OpenAI with good quality",
                "requires_api_key": True,
                "dimension": 1024,
                "pros": ["Good OpenAI alternative", "Competitive pricing"],
                "cons": ["Requires payment", "Less widely used"]
            },
            "anthropic": {
                "name": "Anthropic (NOT AVAILABLE)",
                "description": "Anthropic doesn't currently offer embedding APIs",
                "requires_api_key": False,
                "dimension": None,
                "pros": [],
                "cons": ["Not available for embeddings"]
            }
        }
        return providers

def choose_embedding_provider():
    """Interactive provider selection"""

    print("Available Embedding Providers:")
    print("=" * 50)

    providers = EmbeddingFactory.list_providers()

    for i, (key, info) in enumerate(providers.items(), 1):
        print(f"{i}. {info['name']}")
        print(f"   {info['description']}")
        print(f"   API Key Required: {'Yes' if info['requires_api_key'] else 'No'}")
        if info['dimension']:
            print(f"   Vector Dimension: {info['dimension']}")

        if info['pros']:
            print(f"   Pros: {', '.join(info['pros'])}")
        if info['cons']:
            print(f"   Cons: {', '.join(info['cons'])}")
        print()

    print("Recommendation: Start with HuggingFace (option 1) - it's free and works well!")

    choice = input("Enter choice (1-4): ").strip()

    provider_keys = list(providers.keys())

    try:
        selected_key = provider_keys[int(choice) - 1]
        selected_info = providers[selected_key]

        if selected_key == "anthropic":
            print("❌ Anthropic embeddings are not available")
            print("   Please choose another option")
            return None

        print(f"\nSelected: {selected_info['name']}")

        # Get API key if required
        api_key = None
        if selected_info['requires_api_key']:
            api_key = input("Enter your API key: ").strip()
            if not api_key:
                print("❌ API key required")
                return None

        # Create provider
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key

        provider = EmbeddingFactory.create_provider(selected_key, **kwargs)

        print(f"✓ {selected_info['name']} provider created")
        print(f"  Vector dimension: {provider.get_dimension()}")

        return provider

    except (ValueError, IndexError):
        print("❌ Invalid choice")
        return None
    except Exception as e:
        print(f"❌ Error creating provider: {e}")
        return None

def test_embedding_provider(provider: EmbeddingProvider):
    """Test an embedding provider"""

    print(f"\nTesting embedding provider...")

    test_texts = [
        "The right to vote shall not be denied",
        "Freedom of speech and press",
        "Due process of law"
    ]

    try:
        embeddings = provider.create_embeddings(test_texts)

        if embeddings:
            print(f"✓ Successfully created {len(embeddings)} embeddings")
            print(f"  Dimension: {len(embeddings[0])}")
            print(f"  Sample embedding (first 5 values): {embeddings[0][:5]}")
            return True
        else:
            print("❌ Failed to create embeddings")
            return False

    except Exception as e:
        print(f"❌ Error testing provider: {e}")
        return False

def main():
    print("Embedding Provider Selection Tool")
    print("=" * 40)

    # Show available providers
    provider = choose_embedding_provider()

    if provider:
        # Test the provider
        if test_embedding_provider(provider):
            print(f"\n✅ Provider is working correctly!")
            print(f"\nTo use this provider, update your pinecone_config.py:")
            print(f"  VECTOR_DIMENSION = {provider.get_dimension()}")

            # Save provider config
            config = {
                'provider_type': type(provider).__name__,
                'dimension': provider.get_dimension(),
                'model_name': getattr(provider, 'model_name', 'unknown')
            }

            with open('selected_embedding_provider.json', 'w') as f:
                json.dump(config, f, indent=2)

            print(f"  Configuration saved to: selected_embedding_provider.json")
        else:
            print(f"\n❌ Provider test failed")

if __name__ == "__main__":
    main()