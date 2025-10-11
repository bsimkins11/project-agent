"""Document schemas and types."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentStatus(str, Enum):
    """Document processing status - logical workflow progression."""
    
    # === INITIAL UPLOAD PHASE ===
    UPLOADED = "uploaded"  # Document uploaded, awaiting admin review
    
    # === ACCESS REQUEST PHASE (for Google Drive documents) ===
    REQUEST_ACCESS = "request_access"  # Admin needs to request access to Drive document
    ACCESS_REQUESTED = "access_requested"  # Access request sent to document owner
    ACCESS_GRANTED = "access_granted"  # Document owner granted access
    
    # === APPROVAL PHASE ===
    AWAITING_APPROVAL = "awaiting_approval"  # Ready for admin approval (visible in approval queue)
    APPROVED = "approved"  # Admin approved - document now visible to users in library
    
    # === PROCESSING PHASE (for AI/Chat functionality) ===
    PROCESSING_REQUESTED = "processing_requested"  # Admin requested AI processing
    PROCESSING = "processing"  # Currently being vectorized/processed
    PROCESSED = "processed"  # Fully processed and available for AI chat
    
    # === ERROR STATES ===
    QUARANTINED = "quarantined"  # Removed from system due to policy violations
    FAILED = "failed"  # Processing failed, needs attention


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
    source_uri: Optional[str] = Field(None, description="Source URI (original document link, etc.)")
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
    
    # Document metadata fields for project tracking
    sow_number: Optional[str] = Field(None, description="Statement of Work number")
    deliverable: Optional[str] = Field(None, description="Deliverable description")
    responsible_party: Optional[str] = Field(None, description="Person or team responsible")
    deliverable_id: Optional[str] = Field(None, description="Deliverable identifier")
    link: Optional[str] = Field(None, description="External link to document")
    notes: Optional[str] = Field(None, description="Additional notes or comments")
    web_view_link: Optional[str] = Field(None, description="Web view link for Google Drive documents")
    
    # Google Sheets and Drive specific fields
    sheet_name: Optional[str] = Field(None, description="Google Sheets sheet name if applicable")
    sheet_gid: Optional[str] = Field(None, description="Google Sheets sheet GID if applicable")
    from_sheet_index: bool = Field(default=False, description="Whether document came from a sheet index")
    sheet_index_id: Optional[str] = Field(None, description="ID of the sheet index this document came from")
    drive_file_type: Optional[str] = Field(None, description="Google Drive file type (document, spreadsheet, etc.)")
    is_document_index: bool = Field(default=False, description="Whether this is a document index itself")
    
    # Access request fields for comprehensive workflow
    access_requested: bool = Field(default=False, description="Whether access has been requested")
    access_granted: bool = Field(default=False, description="Whether access has been granted")
    access_requested_at: Optional[datetime] = Field(None, description="When access was requested")
    access_granted_at: Optional[datetime] = Field(None, description="When access was granted")
    access_request_id: Optional[str] = Field(None, description="Unique access request identifier")
    index_source_id: Optional[str] = Field(None, description="ID of the document index this document came from")
    bulk_access_request: bool = Field(default=False, description="Whether this is part of a bulk access request")
    
    # Multi-tenant and RBAC fields (NEW)
    client_id: Optional[str] = Field(None, description="Client/Organization ID - for multi-tenant isolation")
    project_id: Optional[str] = Field(None, description="Project ID - documents belong to specific projects")
    visibility: str = Field(default="project", description="Visibility scope: project|client|public")


class Document(BaseModel):
    """Complete document with metadata and content."""
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    content: Optional[str] = Field(None, description="Extracted text content")
    chunks: List[str] = Field(default_factory=list, description="Text chunks for embedding")
    vector_ids: List[str] = Field(default_factory=list, description="Vector search IDs")
