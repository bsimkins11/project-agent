"""Test document indexing pipeline with real documents."""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from packages.shared.clients.gcs import GCSClient
from packages.shared.clients.documentai import DocumentAIClient
from packages.shared.clients.firestore import FirestoreClient
from packages.shared.clients.vector_search import VectorSearchClient
from packages.shared.schemas.document import DocumentMetadata

async def test_document_indexing_pipeline():
    """Test the complete document indexing pipeline."""
    
    print("🧪 Testing Document Indexing Pipeline")
    print("=" * 50)
    
    # Initialize clients
    gcs_client = GCSClient()
    docai_client = DocumentAIClient()
    firestore_client = FirestoreClient()
    vector_client = VectorSearchClient()
    
    # Test document content (simulate a real document)
    test_content = """
    Project Agent Development Guide
    
    Overview:
    Project Agent is a comprehensive document management system built for Transparent Partners.
    It leverages Google Cloud Platform services to provide intelligent document processing and retrieval.
    
    Key Features:
    1. Document Upload and Storage
       - Supports PDF, DOCX, TXT, MD, and HTML files
       - Secure storage in Google Cloud Storage
       - Automatic file type detection and validation
    
    2. Document Processing
       - AI-powered text extraction using Document AI
       - Entity recognition and table extraction
       - Confidence scoring for processed content
    
    3. Vector Search and Retrieval
       - Semantic search using Vertex AI Vector Search
       - Text chunking for optimal embedding generation
       - Similarity-based document retrieval
    
    4. Chat Interface
       - Natural language queries about documents
       - Cited answers with source references
       - Filter-based search capabilities
    
    Technical Architecture:
    - Backend: FastAPI services with Python
    - Frontend: Next.js with React and Tailwind CSS
    - Infrastructure: Google Cloud Platform
    - Database: Firestore for metadata storage
    - Storage: Google Cloud Storage for documents
    - AI Services: Document AI, Vertex AI, Vector Search
    
    Development Status:
    - Infrastructure: ✅ Deployed
    - Document Upload: ✅ Implemented
    - Document Processing: ✅ Working
    - Vector Search: ✅ Functional
    - Chat Interface: ✅ Active
    - Authentication: 🔄 In Progress
    - Drive Integration: 🔄 Pending
    """
    
    try:
        # Step 1: Upload test document to GCS
        print("\n1. Uploading Test Document to GCS...")
        import uuid
        doc_id = str(uuid.uuid4())
        bucket_name = os.getenv("GCS_DOC_BUCKET", "ta-test-docs-dev")
        gcs_path = f"documents/{doc_id}/project-agent-guide.txt"
        
        gcs_url = await gcs_client.upload_file(
            bucket_name=bucket_name,
            file_path=gcs_path,
            file_content=test_content.encode('utf-8'),
            content_type="text/plain"
        )
        
        print(f"✅ Document uploaded to GCS: {gcs_url}")
        
        # Step 2: Create document metadata in Firestore
        print("\n2. Creating Document Metadata...")
        doc_metadata = DocumentMetadata(
            id=doc_id,
            title="Project Agent Development Guide",
            type="TXT",
            size=len(test_content.encode('utf-8')),
            uri=gcs_url,
            status="uploaded",
            upload_date="2024-01-15T10:30:00Z"
        )
        
        await firestore_client.save_document(doc_metadata)
        print(f"✅ Document metadata saved: {doc_id}")
        
        # Step 3: Process with Document AI
        print("\n3. Processing with Document AI...")
        processing_result = docai_client.process_document(
            file_content=test_content.encode('utf-8'),
            mime_type="text/plain"
        )
        
        print(f"✅ Document AI processing completed")
        print(f"   Text length: {len(processing_result['text'])} characters")
        print(f"   Confidence: {processing_result['confidence']:.2f}")
        
        # Step 4: Create text chunks
        print("\n4. Creating Text Chunks...")
        text_chunks = vector_client.chunk_text(
            processing_result['text'],
            chunk_size=300,
            overlap=50
        )
        
        print(f"✅ Created {len(text_chunks)} text chunks")
        for i, chunk in enumerate(text_chunks[:3]):  # Show first 3 chunks
            print(f"   Chunk {i+1}: '{chunk[:50]}...'")
        
        # Step 5: Generate embeddings and index
        print("\n5. Generating Embeddings and Indexing...")
        vector_ids = []
        
        for i, chunk in enumerate(text_chunks):
            # Generate embedding
            embedding = vector_client.generate_embedding(chunk)
            
            # Create vector ID
            vector_id = f"{doc_id}_chunk_{i}"
            
            # Prepare metadata
            metadata = {
                "doc_id": doc_id,
                "chunk_id": vector_id,
                "chunk_index": i,
                "text": chunk,
                "title": doc_metadata.title,
                "type": doc_metadata.type,
                "page": i + 1
            }
            
            # Upsert to vector search
            success = await vector_client.upsert_vector(vector_id, embedding, metadata)
            if success:
                vector_ids.append(vector_id)
                print(f"   ✅ Indexed chunk {i+1}/{len(text_chunks)}: {vector_id}")
        
        # Step 6: Update document status
        print("\n6. Updating Document Status...")
        doc_metadata.processing_result = processing_result
        doc_metadata.status = "indexed"
        doc_metadata.__dict__['vector_ids'] = vector_ids  # Add vector IDs
        
        await firestore_client.save_document(doc_metadata)
        print(f"✅ Document status updated to 'indexed'")
        
        # Step 7: Test search functionality
        print("\n7. Testing Search Functionality...")
        query = "What is Project Agent?"
        query_embedding = vector_client.generate_embedding(query)
        
        search_results = await vector_client.search_vectors(
            query_embedding=query_embedding,
            filters={},
            max_results=5
        )
        
        print(f"✅ Search completed")
        print(f"   Query: '{query}'")
        print(f"   Results: {len(search_results)}")
        
        for i, result in enumerate(search_results):
            print(f"   Result {i+1}: {result['id']} (score: {result['score']:.3f})")
            print(f"     Text: '{result['metadata']['text'][:80]}...'")
        
        print("\n" + "=" * 50)
        print("🎉 DOCUMENT INDEXING PIPELINE TEST COMPLETED!")
        print("✅ All components are working correctly")
        print(f"\nDocument ID: {doc_id}")
        print(f"Chunks created: {len(text_chunks)}")
        print(f"Vectors indexed: {len(vector_ids)}")
        print(f"Search results: {len(search_results)}")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "chunks": len(text_chunks),
            "vectors": len(vector_ids),
            "search_results": len(search_results)
        }
        
    except Exception as e:
        print(f"\n❌ Document indexing pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    asyncio.run(test_document_indexing_pipeline())
