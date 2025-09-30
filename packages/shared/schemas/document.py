"""Document schemas and types."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    APPROVED = "approved"
    INDEXED = "indexed"
    QUARANTINED = "quarantined"
    FAILED = "failed"


class MediaType(str, Enum):
    """Document media type."""
    DOCUMENT = "document"
    IMAGE = "image"


class DocType(str, Enum):
    """Document type classification."""
    SOW = "sow"
    TIMELINE = "timeline"
    DELIVERABLE = "deliverable"
    MISC = "misc"


class DLPFindings(BaseModel):
    """DLP scan findings."""
    status: str = Field(..., description="DLP scan status")
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="DLP findings")


class EmbeddingInfo(BaseModel):
    """Embedding information."""
    text: Dict[str, int] = Field(..., description="Text embedding counts")


class DocumentMetadata(BaseModel):
    """Document metadata stored in Firestore."""
    doc_id: str = Field(..., description="Unique document identifier")
    media_type: MediaType = Field(..., description="Document media type")
    doc_type: DocType = Field(..., description="Document type classification")
    title: str = Field(..., description="Document title")
    uri: str = Field(..., description="GCS URI for document file")
    source_ref: str = Field(..., description="Source reference (Drive fileId, etc.)")
    status: DocumentStatus = Field(..., description="Processing status")
    required_fields_ok: bool = Field(default=True, description="Required fields validation")
    dlp_scan: DLPFindings = Field(..., description="DLP scan results")
    thumbnails: List[str] = Field(default_factory=list, description="GCS URIs for thumbnails (images only)")
    embeddings: EmbeddingInfo = Field(..., description="Embedding information")
    created_by: str = Field(..., description="Creator email")
    approved_by: List[str] = Field(default_factory=list, description="Approver emails")
    topics: List[str] = Field(default_factory=list, description="Document topics/tags")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class Document(BaseModel):
    """Complete document with metadata and content."""
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    content: Optional[str] = Field(None, description="Extracted text content")
    chunks: List[str] = Field(default_factory=list, description="Text chunks for embedding")
    vector_ids: List[str] = Field(default_factory=list, description="Vector search IDs")
