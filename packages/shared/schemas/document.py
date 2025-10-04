"""Document schemas and types."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PENDING_ACCESS = "pending_access"
    ACCESS_APPROVED = "access_approved"
    PROCESSED = "processed"
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
    id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    type: str = Field(..., description="Document type (PDF, DOCX, etc.)")
    size: int = Field(..., description="File size in bytes")
    uri: str = Field(..., description="GCS URI for document file")
    status: str = Field(..., description="Processing status")
    upload_date: Optional[str] = Field(None, description="Upload date")
    processing_result: Optional[Dict[str, Any]] = Field(None, description="Document AI processing results")
    
    # Optional fields for full implementation
    media_type: Optional[MediaType] = Field(None, description="Document media type")
    doc_type: Optional[DocType] = Field(None, description="Document type classification")
    source_ref: Optional[str] = Field(None, description="Source reference (Drive fileId, etc.)")
    required_fields_ok: bool = Field(default=True, description="Required fields validation")
    dlp_scan: Optional[DLPFindings] = Field(None, description="DLP scan results")
    thumbnails: List[str] = Field(default_factory=list, description="GCS URIs for thumbnails (images only)")
    embeddings: Optional[EmbeddingInfo] = Field(None, description="Embedding information")
    created_by: Optional[str] = Field(None, description="Creator email")
    approved_by: List[str] = Field(default_factory=list, description="Approver emails")
    topics: List[str] = Field(default_factory=list, description="Document topics/tags")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Permission and access control fields
    permission_requested: bool = Field(default=False, description="Whether permission has been requested")
    permission_granted: bool = Field(default=False, description="Whether permission has been granted")
    permission_requested_at: Optional[datetime] = Field(None, description="When permission was requested")
    permission_granted_at: Optional[datetime] = Field(None, description="When permission was granted")
    drive_file_id: Optional[str] = Field(None, description="Google Drive file ID if applicable")
    requires_permission: bool = Field(default=False, description="Whether document requires permission access")
    
    # Access request fields for comprehensive workflow
    access_requested: bool = Field(default=False, description="Whether access has been requested")
    access_granted: bool = Field(default=False, description="Whether access has been granted")
    access_requested_at: Optional[datetime] = Field(None, description="When access was requested")
    access_granted_at: Optional[datetime] = Field(None, description="When access was granted")
    access_request_id: Optional[str] = Field(None, description="Unique access request identifier")
    index_source_id: Optional[str] = Field(None, description="ID of the document index this document came from")
    bulk_access_request: bool = Field(default=False, description="Whether this is part of a bulk access request")


class Document(BaseModel):
    """Complete document with metadata and content."""
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    content: Optional[str] = Field(None, description="Extracted text content")
    chunks: List[str] = Field(default_factory=list, description="Text chunks for embedding")
    vector_ids: List[str] = Field(default_factory=list, description="Vector search IDs")
