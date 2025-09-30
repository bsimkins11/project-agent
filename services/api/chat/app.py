"""Chat API service for Project Agent."""

import time
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware

from packages.shared.schemas import ChatRequest, ChatResponse, Citation
from packages.shared.clients.auth import require_domain_auth

app = FastAPI(
    title="Project Agent Chat API",
    description="AI-powered chat with cited answers from document knowledge base",
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


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: Dict[str, Any] = Depends(require_domain_auth)
) -> ChatResponse:
    """
    Process chat query and return AI-generated answer with citations.
    
    Args:
        request: Chat request with query and filters
        user: Authenticated user info
        
    Returns:
        Chat response with answer and citations
    """
    start_time = time.time()
    
    try:
        # Placeholder implementation
        # In production, use ADK planner to process the query
        answer = f"Based on your query '{request.query}', here's what I found in the knowledge base..."
        
        # Mock citations for now
        citations = [
            Citation(
                doc_id="doc-001",
                title="Sample Document",
                uri="gs://bucket/sample.pdf",
                page=1,
                excerpt="Relevant excerpt from the document...",
                thumbnail=None
            )
        ]
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            answer=answer,
            citations=citations,
            query_time_ms=query_time_ms,
            total_results=len(citations)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chat-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
