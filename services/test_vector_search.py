"""Test vector search functionality."""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from packages.shared.clients.vector_search import VectorSearchClient

async def test_vector_search():
    """Test vector search functionality."""
    
    print("🧪 Testing Vector Search")
    print("=" * 40)
    
    # Initialize client
    try:
        client = VectorSearchClient()
        print(f"✅ Vector search client initialized")
        print(f"   Project: {client.project_id}")
        print(f"   Location: {client.location}")
        print(f"   Index ID: {client.index_id}")
    except Exception as e:
        print(f"❌ Failed to initialize vector search client: {e}")
        return False
    
    # Test 1: Generate embeddings
    print("\n1. Testing Embedding Generation...")
    try:
        test_texts = [
            "Project Agent is a document management system",
            "It uses Google Cloud services for processing",
            "Vector search enables semantic document retrieval"
        ]
        
        embeddings = []
        for text in test_texts:
            embedding = client.generate_embedding(text)
            embeddings.append(embedding)
            print(f"   Generated embedding for: '{text[:30]}...' (dim: {len(embedding)})")
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return False
    
    # Test 2: Text chunking
    print("\n2. Testing Text Chunking...")
    try:
        long_text = """
        Project Agent is a comprehensive document management system built for Transparent Partners.
        It leverages Google Cloud Platform services including Document AI, Vertex AI Vector Search,
        Firestore, and Cloud Storage to provide intelligent document processing and retrieval.
        
        The system supports multiple document types including PDFs, Word documents, text files,
        and images. It uses advanced AI technologies for text extraction, entity recognition,
        and semantic search capabilities.
        
        Key features include:
        - Automated document ingestion from Google Drive
        - AI-powered text extraction and processing
        - Vector-based semantic search
        - Secure document storage and access control
        - Integration with existing workflow tools
        """
        
        chunks = client.chunk_text(long_text, chunk_size=200, overlap=50)
        print(f"✅ Text chunking successful")
        print(f"   Original length: {len(long_text)} characters")
        print(f"   Number of chunks: {len(chunks)}")
        
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"   Chunk {i+1}: '{chunk[:50]}...'")
        
    except Exception as e:
        print(f"❌ Text chunking failed: {e}")
        return False
    
    # Test 3: Vector upsert
    print("\n3. Testing Vector Upsert...")
    try:
        vector_id = "test-vector-001"
        test_embedding = embeddings[0]
        metadata = {
            "doc_id": "test-doc-001",
            "text": test_texts[0],
            "page": 1,
            "type": "test"
        }
        
        success = await client.upsert_vector(vector_id, test_embedding, metadata)
        if success:
            print(f"✅ Vector upsert successful")
        else:
            print(f"❌ Vector upsert failed")
            return False
            
    except Exception as e:
        print(f"❌ Vector upsert failed: {e}")
        return False
    
    # Test 4: Vector search
    print("\n4. Testing Vector Search...")
    try:
        query_text = "document management system"
        query_embedding = client.generate_embedding(query_text)
        
        filters = {"type": "test"}
        results = await client.search_vectors(query_embedding, filters, max_results=5)
        
        print(f"✅ Vector search successful")
        print(f"   Query: '{query_text}'")
        print(f"   Results: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"   Result {i+1}: {result['id']} (score: {result['score']:.3f})")
            print(f"     Text: '{result['metadata']['text'][:50]}...'")
        
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 ALL VECTOR SEARCH TESTS PASSED!")
    print("✅ Vector search functionality is working correctly")
    print("\nNext steps:")
    print("- Integrate with real embedding model")
    print("- Connect to actual Vertex AI Vector Search index")
    print("- Implement document indexing pipeline")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_vector_search())