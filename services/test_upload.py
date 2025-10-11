"""Test document upload functionality."""

import os
import sys
import asyncio

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from packages.shared.clients.documentai import DocumentAIClient
from packages.shared.clients.gcs import GCSClient
from packages.shared.clients.firestore import FirestoreClient
from packages.shared.schemas.document import DocumentMetadata

async def test_document_processing():
    """Test Document AI processing with a sample PDF."""
    
    print("🧪 Testing Document Processing Pipeline")
    print("=" * 50)
    
    # Initialize clients
    docai_client = DocumentAIClient()
    gcs_client = GCSClient()
    firestore_client = FirestoreClient()
    
    # Test 1: Document AI Processing
    print("\n1. Testing Document AI Processing...")
    try:
        # Create a simple test document content (simulating a PDF)
        test_content = b"""Sample Document
        
This is a test document for Project Agent.
It contains multiple paragraphs and should be processed by Document AI.

Key Points:
- Document processing works
- Text extraction is functional
- Entity recognition is active

Conclusion: The system is working as expected."""
        
        # Process with Document AI
        result = docai_client.process_document(
            file_content=test_content,
            mime_type="text/plain"
        )
        
        print(f"✅ Document AI processing successful")
        print(f"   Text length: {len(result['text'])} characters")
        print(f"   Pages: {result['page_count']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Entities: {len(result['entities'])}")
        print(f"   Tables: {len(result['tables'])}")
        
        if result.get('error'):
            print(f"⚠️  Processing warning: {result['error']}")
        
    except Exception as e:
        print(f"❌ Document AI processing failed: {e}")
        return False
    
    # Test 2: GCS Upload
    print("\n2. Testing GCS Upload...")
    try:
        bucket_name = os.getenv("GCS_DOC_BUCKET", "ta-test-docs-dev")
        file_path = "test/sample-document.txt"
        
        gcs_url = await gcs_client.upload_file(
            bucket_name=bucket_name,
            file_path=file_path,
            file_content=test_content,
            content_type="text/plain"
        )
        
        print(f"✅ GCS upload successful")
        print(f"   URL: {gcs_url}")
        
    except Exception as e:
        print(f"❌ GCS upload failed: {e}")
        return False
    
    # Test 3: Firestore Storage
    print("\n3. Testing Firestore Storage...")
    try:
        doc_metadata = DocumentMetadata(
            id="test-doc-001",
            title="Sample Test Document",
            type="TXT",
            size=len(test_content),
            uri=gcs_url,
            status="processed",
            upload_date="2024-01-15T10:30:00Z",
            processing_result=result
        )
        
        doc_id = await firestore_client.save_document(doc_metadata)
        
        print(f"✅ Firestore storage successful")
        print(f"   Document ID: {doc_id}")
        
        # Retrieve the document
        retrieved_doc = await firestore_client.get_document(doc_id)
        if retrieved_doc:
            print(f"✅ Document retrieval successful")
            print(f"   Title: {retrieved_doc.title}")
            print(f"   Status: {retrieved_doc.status}")
        else:
            print(f"❌ Document retrieval failed")
            return False
        
    except Exception as e:
        print(f"❌ Firestore storage failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED!")
    print("✅ Document processing pipeline is working correctly")
    print("\nNext steps:")
    print("- Test with real PDF files")
    print("- Implement vector embeddings")
    print("- Set up search functionality")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_document_processing())
