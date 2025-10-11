"""Simple Documents API service for Project Agent."""

from fastapi import FastAPI, HTTPException, Depends, status, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from datetime import datetime

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

# Mock authentication dependency
async def require_domain_auth():
    """Mock authentication for demo purposes."""
    return {"user": "demo@transparent.partners", "domain": "transparent.partners"}

# Mock Firestore client
class MockFirestoreClient:
    async def query_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Mock query documents by category."""
        # Return mock data for demo
        mock_documents = [
            {
                "id": f"doc-{category}-001",
                "title": f"Sample {category.title()} Document 1",
                "type": "PDF",
                "upload_date": "2024-01-15",
                "size": 1024000,
                "status": "indexed",
                "doc_type": category,
                "created_by": "admin@transparent.partners",
                "source_ref": f"https://docs.google.com/document/d/sample-{category}-1"
            },
            {
                "id": f"doc-{category}-002", 
                "title": f"Sample {category.title()} Document 2",
                "type": "DOCX",
                "upload_date": "2024-01-20",
                "size": 512000,
                "status": "indexed",
                "doc_type": category,
                "created_by": "admin@transparent.partners",
                "source_ref": f"https://docs.google.com/document/d/sample-{category}-2"
            }
        ]
        return mock_documents

firestore = MockFirestoreClient()

@app.get("/documents/{doc_id}")
async def get_document(
    doc_id: str = Path(..., description="Document ID"),
    user: dict = Depends(require_domain_auth)
) -> Dict[str, Any]:
    """
    Get document details and metadata.
    """
    # Mock document response
    return {
        "id": doc_id,
        "title": f"Sample Document {doc_id}",
        "type": "PDF",
        "content": "This is mock document content...",
        "metadata": {
            "upload_date": "2024-01-15",
            "size": 1024000,
            "status": "indexed",
            "doc_type": "sow",
            "created_by": "admin@transparent.partners"
        }
    }

@app.get("/documents/by-category/{category}")
async def get_documents_by_category(
    category: str = Path(..., description="Document category"),
    user: dict = Depends(require_domain_auth)
) -> Dict[str, Any]:
    """
    Get documents by category for end users.
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

        # Format documents for frontend
        formatted_documents = []
        for doc in documents:
            formatted_doc = {
                "id": doc.get("id"),
                "title": doc.get("title"),
                "type": doc.get("type"),
                "upload_date": doc.get("upload_date"),
                "size": doc.get("size"),
                "status": doc.get("status"),
                "doc_type": doc.get("doc_type"),
                "created_by": doc.get("created_by"),
                "webViewLink": doc.get("source_ref")
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
