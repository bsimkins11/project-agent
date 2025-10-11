"""Chat API service for Project Agent with RBAC filtering."""

import time
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from packages.shared.schemas import ChatRequest, ChatResponse, Citation
from packages.shared.clients.auth import require_domain_auth, get_user_context, filter_documents_by_access
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
    Results are filtered by user's RBAC permissions to only include accessible documents.
    
    Args:
        request: Chat request with query and filters
        user: Authenticated user info with RBAC context
        
    Returns:
        Chat response with answer and citations from accessible documents only
    """
    start_time = time.time()
    
    try:
        # Get user RBAC context
        user_context = await get_user_context(user.get("email", ""))
        
        # Add user context to filters so agent planner can limit search
        enhanced_filters = request.filters or {}
        enhanced_filters["user_project_ids"] = user_context.get("project_ids", [])
        enhanced_filters["user_client_ids"] = user_context.get("client_ids", [])
        enhanced_filters["user_role"] = user_context.get("role", "")
        
        # Use agent planner to process the query
        user_id = user.get("email", "anonymous")
        agent_result = await agent_planner.process_query(
            query=request.query,
            filters=enhanced_filters,
            max_results=10,
            user_id=user_id
        )
        
        # Convert agent snippets to citations
        # Filter citations to only include documents user has access to
        all_citations = []
        for snippet in agent_result["snippets"]:
            all_citations.append({
                "doc_id": snippet["doc_id"],
                "title": snippet["title"],
                "uri": snippet["uri"],
                "page": snippet["page"],
                "excerpt": snippet["excerpt"],
                "thumbnail": snippet["thumbnail"]
            })
        
        # Apply RBAC filtering to citations
        accessible_citations = await filter_documents_by_access(
            user["email"],
            all_citations
        )
        
        # Convert to Citation objects
        citations = [
            Citation(
                doc_id=c["doc_id"],
                title=c["title"],
                uri=c["uri"],
                page=c["page"],
                excerpt=c["excerpt"],
                thumbnail=c.get("thumbnail")
            )
            for c in accessible_citations
        ]
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            answer=agent_result["answer"],
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
