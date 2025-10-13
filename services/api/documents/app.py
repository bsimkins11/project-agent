"""Documents API service for Project Agent with RBAC access control."""

from fastapi import FastAPI, HTTPException, Depends, status, Path
from fastapi.middleware.cors import CORSMiddleware

from packages.shared.schemas import Document, DocumentMetadata
from packages.shared.clients.firestore import FirestoreClient
from packages.shared.clients.gcs import GCSClient
from packages.shared.clients.auth import require_domain_auth, check_document_access, filter_documents_by_access

app = FastAPI(
    title="Project Agent Documents API",
    description="Document details and management service",
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
firestore = FirestoreClient()
gcs = GCSClient()


@app.get("/documents/{doc_id}", response_model=Document)
async def get_document(
    doc_id: str = Path(..., description="Document ID"),
    user: dict = Depends(require_domain_auth)
) -> Document:
    """
    Get document details and metadata with RBAC access control.
    Users can only access documents in their assigned projects/clients.
    """
    try:
        # Check if user has access to this document (POC: full access, Portal: JWT-based)
        has_access = check_document_access(user["email"], doc_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to document: {doc_id}"
            )
        
        # Get document metadata from Firestore
        metadata = await firestore.get_document_metadata(doc_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        # Get document content from GCS
        content = await gcs.get_document_content(metadata.uri)
        
        # Get text chunks if available
        chunks = await firestore.get_document_chunks(doc_id)
        
        # Get vector IDs
        vector_ids = await firestore.get_document_vectors(doc_id)
        
        document = Document(
            metadata=metadata,
            content=content,
            chunks=chunks,
            vector_ids=vector_ids
        )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document retrieval failed: {str(e)}"
        )


@app.get("/documents/by-category/{category}")
async def get_documents_by_category(
    category: str = Path(..., description="Document category"),
    user: dict = Depends(require_domain_auth)
) -> dict:
    """
    Get documents by category for end users with RBAC filtering.
    Users see only documents they have access to.
    """
    try:
        # Validate category
        valid_categories = ["sow", "timeline", "deliverable", "misc"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )
        
        # Query documents by category
        documents = await firestore.query_documents_by_category(category)
        
        # Filter documents by user access (POC: full access, Portal: JWT-based)
        accessible_docs = filter_documents_by_access(user["email"], documents)
        
        # Format documents for frontend
        formatted_documents = []
        for doc in accessible_docs:
            formatted_doc = {
                "id": doc.get("id"),
                "title": doc.get("title"),
                "type": doc.get("type"),
                "upload_date": doc.get("upload_date"),
                "size": doc.get("size"),
                "status": doc.get("status"),
                "doc_type": doc.get("doc_type"),
                "created_by": doc.get("created_by"),
                "webViewLink": doc.get("source_ref")  # Use source_ref as webViewLink if available
            }
            formatted_documents.append(formatted_doc)
        
        return {
            "category": category,
            "documents": formatted_documents,
            "total": len(formatted_documents)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents by category: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "documents-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
