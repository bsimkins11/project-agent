"""Simple Chat API for document ingestion testing."""

import os
import time
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Project Agent Chat API",
    description="Simple chat API for document ingestion testing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    filters: Dict[str, Any] = {}

class Citation(BaseModel):
    doc_id: str
    title: str
    uri: str
    page: int
    excerpt: str
    thumbnail: str = None
    web_view_link: str = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    query_time_ms: int
    total_results: int

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Simple chat endpoint for testing."""
    start_time = time.time()
    
    # Mock response with document citations
    answer = f"Based on your query '{request.query}', I found relevant information in the following documents:\n\n"
    
    # Mock citations with web view links
    citations = [
        Citation(
            doc_id="doc-sow-001",
            title="Project SOW v1.0",
            uri="gs://ta-test-docs-uat/sow/project-sow-v1.pdf",
            page=1,
            excerpt="This document contains the project scope, objectives, and deliverables for the current engagement.",
            web_view_link="https://drive.google.com/file/d/sample-sow-1/view"
        ),
        Citation(
            doc_id="doc-timeline-001",
            title="Project Timeline",
            uri="gs://ta-test-docs-uat/timeline/project-timeline.pdf",
            page=2,
            excerpt="The project timeline outlines key milestones and delivery dates for all phases.",
            web_view_link="https://drive.google.com/file/d/sample-timeline-1/view"
        )
    ]
    
    # Add citations to answer
    for i, citation in enumerate(citations, 1):
        answer += f"{i}. **{citation.title}** (Page {citation.page})\n"
        answer += f"   {citation.excerpt}\n"
        answer += f"   [View Document]({citation.web_view_link})\n\n"
    
    query_time_ms = int((time.time() - start_time) * 1000)
    
    return ChatResponse(
        answer=answer,
        citations=citations,
        query_time_ms=query_time_ms,
        total_results=len(citations)
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chat-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
