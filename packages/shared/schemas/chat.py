"""Chat API schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation for a chat response."""
    doc_id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    uri: str = Field(..., description="Document URI or signed URL")
    page: Optional[int] = Field(None, description="Page number for documents")
    excerpt: str = Field(..., description="Relevant text excerpt")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL for images")


class ChatRequest(BaseModel):
    """Chat API request."""
    query: str = Field(..., description="User query", min_length=1)
    filters: Optional[Dict[str, Any]] = Field(None, description="Query filters")
    max_results: int = Field(default=10, description="Maximum results to return", ge=1, le=50)


class ChatResponse(BaseModel):
    """Chat API response."""
    answer: str = Field(..., description="AI-generated answer")
    citations: List[Citation] = Field(..., description="Source citations")
    query_time_ms: int = Field(..., description="Query processing time in milliseconds")
    total_results: int = Field(..., description="Total matching results found")
