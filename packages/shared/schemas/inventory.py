"""Inventory API schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .document import DocType, MediaType, DocumentStatus


class InventoryFilters(BaseModel):
    """Inventory filtering options."""
    doc_type: Optional[DocType] = Field(None, description="Filter by document type")
    media_type: Optional[MediaType] = Field(None, description="Filter by media type")
    status: Optional[DocumentStatus] = Field(None, description="Filter by status")
    q: Optional[str] = Field(None, description="Search query")
    created_by: Optional[str] = Field(None, description="Filter by creator")
    topics: Optional[List[str]] = Field(None, description="Filter by topics")


class InventoryRequest(BaseModel):
    """Inventory API request."""
    filters: Optional[InventoryFilters] = Field(None, description="Filtering options")
    page: int = Field(default=1, description="Page number", ge=1)
    page_size: int = Field(default=20, description="Items per page", ge=1, le=100)
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


class InventoryItem(BaseModel):
    """Inventory item summary."""
    doc_id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    doc_type: DocType = Field(..., description="Document type")
    media_type: MediaType = Field(..., description="Media type")
    status: DocumentStatus = Field(..., description="Processing status")
    created_by: str = Field(..., description="Creator")
    created_at: str = Field(..., description="Creation date")
    topics: List[str] = Field(default_factory=list, description="Topics")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")


class InventoryResponse(BaseModel):
    """Inventory API response."""
    items: List[InventoryItem] = Field(..., description="Inventory items")
    total: int = Field(..., description="Total items matching filters")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total pages")
