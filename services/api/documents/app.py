"""Documents API service for Project Agent."""

from fastapi import FastAPI, HTTPException, Depends, status, Path
from fastapi.middleware.cors import CORSMiddleware

from packages.shared.schemas import Document, DocumentMetadata
from packages.shared.clients.firestore import FirestoreClient
from packages.shared.clients.gcs import GCSClient
from packages.shared.clients.auth import require_domain_auth

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
    Get document details and metadata.
    """
    try:
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "documents-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
