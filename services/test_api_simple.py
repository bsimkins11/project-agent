"""Simple test API without authentication dependencies."""

from fastapi import FastAPI
from typing import Dict, Any
import time

app = FastAPI(title="Project Agent Test API")

@app.post("/chat")
async def chat_test(request: Dict[str, Any]) -> Dict[str, Any]:
    """Test chat endpoint with mock response."""
    start_time = time.time()
    
    # Mock response
    answer = f"Based on your query '{request.get('query', 'test')}', here's what I found in the knowledge base..."
    
    citations = [
        {
            "doc_id": "doc-001",
            "title": "Sample Document",
            "uri": "gs://ta-test-docs-dev/sample.pdf",
            "page": 1,
            "excerpt": "Relevant excerpt from the document...",
            "thumbnail": None
        }
    ]
    
    query_time_ms = int((time.time() - start_time) * 1000)
    
    return {
        "answer": answer,
        "citations": citations,
        "query_time_ms": query_time_ms,
        "total_results": len(citations)
    }

@app.get("/inventory")
async def inventory_test() -> Dict[str, Any]:
    """Test inventory endpoint."""
    return {
        "documents": [
            {
                "id": "doc-001",
                "title": "Sample Document",
                "type": "PDF",
                "upload_date": "2024-01-15T10:30:00Z",
                "size": 1024000,
                "status": "processed"
            }
        ],
        "total": 1,
        "filters": {
            "types": ["PDF", "DOCX", "TXT", "MD", "HTML"],
            "statuses": ["processed", "pending", "failed"]
        }
    }

@app.get("/documents/{doc_id}")
async def document_detail(doc_id: str) -> Dict[str, Any]:
    """Test document detail endpoint."""
    return {
        "id": doc_id,
        "title": f"Document {doc_id}",
        "content": "This is the full content of the document...",
        "metadata": {
            "type": "PDF",
            "size": 1024000,
            "upload_date": "2024-01-15T10:30:00Z",
            "pages": 5
        },
        "chunks": [
            {
                "id": "chunk-1",
                "text": "First chunk of content...",
                "page": 1,
                "score": 0.95
            }
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "project-agent-api"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Project Agent API is running!", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
