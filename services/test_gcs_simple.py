"""Simple GCS test to debug the bucket name issue."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from packages.shared.clients.gcs import GCSClient

async def test_gcs_upload():
    """Test GCS upload functionality."""
    
    print("🧪 Testing GCS Upload")
    print("=" * 30)
    
    print(f"GCP_PROJECT: {os.getenv('GCP_PROJECT')}")
    print(f"GCS_DOC_BUCKET: {os.getenv('GCS_DOC_BUCKET')}")
    
    # Initialize GCS client
    try:
        client = GCSClient()
        print(f"✅ GCS client initialized")
        print(f"   Project ID: {client.project_id}")
    except Exception as e:
        print(f"❌ Failed to initialize GCS client: {e}")
        return False
    
    # Test upload
    try:
        test_content = b"Hello, this is a test document for Project Agent!"
        bucket_name = os.getenv("GCS_DOC_BUCKET", "ta-test-docs-dev")
        file_path = "test/simple-test.txt"
        
        print(f"\n📤 Uploading to bucket: {bucket_name}")
        print(f"   Path: {file_path}")
        
        gcs_url = await client.upload_file(
            bucket_name=bucket_name,
            file_path=file_path,
            file_content=test_content,
            content_type="text/plain"
        )
        
        print(f"✅ Upload successful!")
        print(f"   URL: {gcs_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_gcs_upload())
