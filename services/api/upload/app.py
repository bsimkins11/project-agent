"""Document upload API service for Project Agent with RBAC authorization."""

import os
import uuid
from typing import Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from packages.shared.clients.gcs import GCSClient
from packages.shared.clients.documentai import DocumentAIClient
from packages.shared.clients.firestore import FirestoreClient
from packages.shared.schemas.document import DocumentMetadata
from packages.shared.clients.auth import require_domain_auth

app = FastAPI(
    title="Project Agent Upload API",
    description="Document upload and processing service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://transparent-agent-test.web.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
gcs_client = GCSClient()
docai_client = DocumentAIClient()
firestore_client = FirestoreClient()

# Supported file types for v1
SUPPORTED_TYPES = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "text/plain": "TXT",
    "text/markdown": "MD",
    "text/html": "HTML"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: dict = Depends(require_domain_auth)
) -> Dict[str, Any]:
    """
    Upload and process a document. POC: All authenticated users can upload.
    Only Project Admins and Super Admins can upload documents.
    
    Args:
        file: The uploaded file
        user: Authenticated user with UPLOAD_DOCUMENTS permission
        
    Returns:
        Document metadata and processing results
    """
    try:
        # Validate file type
        if file.content_type not in SUPPORTED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}. Supported types: {list(SUPPORTED_TYPES.keys())}"
            )
        
        # Validate file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        
        # Upload to GCS
        bucket_name = os.getenv("GCS_DOC_BUCKET", "ta-test-docs-dev")
        gcs_path = f"documents/{doc_id}/{file.filename}"
        
        print(f"Uploading to bucket: {bucket_name}, path: {gcs_path}")
        
        try:
            gcs_url = await gcs_client.upload_file(
                bucket_name=bucket_name,
                file_path=gcs_path,
                file_content=file_content,
                content_type=file.content_type
            )
            print(f"✅ GCS upload successful: {gcs_url}")
        except Exception as e:
            print(f"❌ GCS upload failed: {e}")
            raise
        
        # Process with Document AI
        print(f"Processing with Document AI...")
        try:
            processing_result = docai_client.process_document(
                file_content=file_content,
                mime_type=file.content_type
            )
            print(f"✅ Document AI processing completed")
        except Exception as e:
            print(f"❌ Document AI processing failed: {e}")
            processing_result = {"error": str(e), "text": "", "pages": [], "entities": [], "tables": [], "confidence": 0.0, "page_count": 0}
        
        # Create document metadata
        doc_metadata = DocumentMetadata(
            id=doc_id,
            title=file.filename,
            type=SUPPORTED_TYPES[file.content_type],
            size=len(file_content),
            uri=gcs_url,
            status="processed" if not processing_result.get("error") else "failed",
            upload_date=processing_result.get("upload_date"),
            processing_result=processing_result
        )
        
        # Store in Firestore
        await firestore_client.save_document(doc_metadata)
        
        return {
            "success": True,
            "document_id": doc_id,
            "title": file.filename,
            "type": SUPPORTED_TYPES[file.content_type],
            "size": len(file_content),
            "status": doc_metadata.status,
            "gcs_url": gcs_url,
            "processing_result": processing_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@app.get("/upload/status/{document_id}")
async def get_upload_status(document_id: str) -> Dict[str, Any]:
    """
    Get the processing status of an uploaded document.
    
    Args:
        document_id: The document ID
        
    Returns:
        Document status and metadata
    """
    try:
        doc_metadata = await firestore_client.get_document(document_id)
        if not doc_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {
            "document_id": document_id,
            "status": doc_metadata.status,
            "title": doc_metadata.title,
            "type": doc_metadata.type,
            "size": doc_metadata.size,
            "upload_date": doc_metadata.upload_date,
            "processing_result": doc_metadata.processing_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "upload-api"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Project Agent Upload API is running!", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
