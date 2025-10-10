"""Chat API service for Project Agent."""

import time
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from packages.shared.schemas import ChatRequest, ChatResponse, Citation
from packages.shared.clients.auth import require_domain_auth
from packages.shared.clients.vector_search import VectorSearchClient
from packages.shared.clients.firestore import FirestoreClient
from packages.agent_core import ADKPlanner

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

# Initialize clients
vector_client = VectorSearchClient()
firestore_client = FirestoreClient()
agent_planner = ADKPlanner()


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
        # Use agent planner to process the query
        user_id = user.get("email", "anonymous")
        agent_result = await agent_planner.process_query(
            query=request.query,
            filters=request.filters or {},
            max_results=10,
            user_id=user_id
        )
        
        # Convert agent snippets to citations
        citations = []
        for snippet in agent_result["snippets"]:
            citation = Citation(
                doc_id=snippet["doc_id"],
                title=snippet["title"],
                uri=snippet["uri"],
                page=snippet["page"],
                excerpt=snippet["excerpt"],
                thumbnail=snippet["thumbnail"]
            )
            citations.append(citation)
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            answer=agent_result["answer"],
            citations=citations,
            query_time_ms=query_time_ms,
            total_results=agent_result["total_results"]
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
