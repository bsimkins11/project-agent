"""Simple upload API test."""

import os
import sys
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from packages.shared.clients.gcs import GCSClient
from packages.shared.schemas.document import DocumentMetadata

app = FastAPI()

# Initialize clients
gcs_client = GCSClient()

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Simple upload endpoint."""
    try:
        print(f"📁 Received file: {file.filename}, type: {file.content_type}")
        
        # Read file content
        file_content = await file.read()
        print(f"📄 File size: {len(file_content)} bytes")
        
        # Generate document ID
        doc_id = str(uuid.uuid4())
        print(f"🆔 Generated doc ID: {doc_id}")
        
        # Upload to GCS
        bucket_name = os.getenv("GCS_DOC_BUCKET", "ta-test-docs-dev")
        gcs_path = f"documents/{doc_id}/{file.filename}"
        
        print(f"📤 Uploading to GCS: {bucket_name}/{gcs_path}")
        
        gcs_url = await gcs_client.upload_file(
            bucket_name=bucket_name,
            file_path=gcs_path,
            file_content=file_content,
            content_type=file.content_type
        )
        
        print(f"✅ GCS upload successful: {gcs_url}")
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "size": len(file_content),
            "gcs_url": gcs_url
        }
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)
