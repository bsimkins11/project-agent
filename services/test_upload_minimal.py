"""Minimal upload test to isolate the issue."""

import os
import sys
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from packages.shared.clients.gcs import GCSClient
from packages.shared.schemas.document import DocumentMetadata

async def test_minimal_upload():
    """Test minimal upload functionality."""
    
    print("🧪 Testing Minimal Upload")
    print("=" * 30)
    
    # Test 1: GCS Upload
    print("\n1. Testing GCS Upload...")
    try:
        gcs_client = GCSClient()
        test_content = b"Hello, this is a test document!"
        doc_id = str(uuid.uuid4())
        bucket_name = os.getenv("GCS_DOC_BUCKET", "ta-test-docs-dev")
        gcs_path = f"documents/{doc_id}/test.txt"
        
        gcs_url = await gcs_client.upload_file(
            bucket_name=bucket_name,
            file_path=gcs_path,
            file_content=test_content,
            content_type="text/plain"
        )
        
        print(f"✅ GCS upload successful: {gcs_url}")
        
    except Exception as e:
        print(f"❌ GCS upload failed: {e}")
        return False
    
    # Test 2: DocumentMetadata Creation
    print("\n2. Testing DocumentMetadata Creation...")
    try:
        doc_metadata = DocumentMetadata(
            id=doc_id,
            title="Test Document",
            type="TXT",
            size=len(test_content),
            uri=gcs_url,
            status="processed",
            upload_date="2024-01-15T10:30:00Z",
            processing_result={"text": "test content", "pages": [], "entities": [], "tables": [], "confidence": 0.0, "page_count": 1}
        )
        
        print(f"✅ DocumentMetadata created successfully")
        print(f"   ID: {doc_metadata.id}")
        print(f"   Title: {doc_metadata.title}")
        print(f"   URI: {doc_metadata.uri}")
        
    except Exception as e:
        print(f"❌ DocumentMetadata creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_minimal_upload())
