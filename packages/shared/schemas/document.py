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


class DocumentCategory(str, Enum):
    """High-level document categories."""
    PROJECT_MANAGEMENT = "project_management"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    COMMUNICATION = "communication"
    LEGAL_COMPLIANCE = "legal_compliance"
    DATA_ANALYSIS = "data_analysis"
    MEDIA_ASSETS = "media_assets"
    MISCELLANEOUS = "miscellaneous"


class DocumentSubcategory(str, Enum):
    """Document subcategories for more granular classification."""
    # Project Management subcategories
    PLANNING = "planning"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    CLOSURE = "closure"
    
    # Financial subcategories
    BUDGETING = "budgeting"
    BILLING = "billing"
    REPORTING = "reporting"
    AUDIT = "audit"
    
    # Technical subcategories
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    
    # Communication subcategories
    INTERNAL = "internal"
    EXTERNAL = "external"
    CLIENT = "client"
    STAKEHOLDER = "stakeholder"
    
    # Legal/Compliance subcategories
    CONTRACTS = "contracts"
    POLICIES = "policies"
    REGULATORY = "regulatory"
    RISK = "risk"
    
    # Data/Analysis subcategories
    COLLECTION = "collection"
    PROCESSING = "processing"
    VISUALIZATION = "visualization"
    INSIGHTS = "insights"
    
    # Media/Assets subcategories
    CREATIVE = "creative"
    MARKETING = "marketing"
    TRAINING = "training"
    REFERENCE = "reference"


class DocType(str, Enum):
    """Document type classification."""
    # Project Management Documents
    SOW = "sow"  # Statement of Work
    TIMELINE = "timeline"  # Project timeline/schedule
    DELIVERABLE = "deliverable"  # Project deliverables
    MILESTONE = "milestone"  # Project milestones
    REQUIREMENTS = "requirements"  # Requirements documents
    SPECIFICATION = "specification"  # Technical specifications
    
    # Financial Documents
    BUDGET = "budget"  # Budget documents
    INVOICE = "invoice"  # Invoices and billing
    EXPENSE = "expense"  # Expense reports
    FINANCIAL_REPORT = "financial_report"  # Financial reports
    
    # Technical Documents
    TECHNICAL_DOC = "technical_doc"  # Technical documentation
    API_DOC = "api_doc"  # API documentation
    USER_GUIDE = "user_guide"  # User guides and manuals
    ARCHITECTURE = "architecture"  # System architecture docs
    DESIGN_DOC = "design_doc"  # Design documents
    
    # Communication Documents
    EMAIL = "email"  # Email communications
    MEETING_NOTES = "meeting_notes"  # Meeting notes/minutes
    PRESENTATION = "presentation"  # Presentations/slides
    REPORT = "report"  # General reports
    
    # Legal and Compliance
    CONTRACT = "contract"  # Contracts and agreements
    LEGAL_DOC = "legal_doc"  # Legal documents
    POLICY = "policy"  # Policies and procedures
    COMPLIANCE = "compliance"  # Compliance documents
    
    # Data and Analysis
    DATA_SHEET = "data_sheet"  # Data sheets and spreadsheets
    ANALYSIS = "analysis"  # Analysis reports
    RESEARCH = "research"  # Research documents
    SURVEY = "survey"  # Survey results
    
    # Media and Assets
    IMAGE = "image"  # Images and graphics
    VIDEO = "video"  # Video files
    AUDIO = "audio"  # Audio files
    DIAGRAM = "diagram"  # Diagrams and flowcharts
    
    # Miscellaneous
    MISC = "misc"  # Miscellaneous documents
    TEMPLATE = "template"  # Document templates
    FORM = "form"  # Forms and templates


class DLPFindings(BaseModel):
    """DLP scan findings."""
    status: str = Field(..., description="DLP scan status")
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="DLP findings")


class EmbeddingInfo(BaseModel):
    """Embedding information."""
    text: Dict[str, int] = Field(..., description="Text embedding counts")


class ClassificationInfo(BaseModel):
    """Document classification information."""
    doc_type: DocType = Field(..., description="Primary document type")
    category: DocumentCategory = Field(..., description="Document category")
    subcategory: Optional[DocumentSubcategory] = Field(None, description="Document subcategory")
    confidence_score: float = Field(..., description="Classification confidence (0.0-1.0)", ge=0.0, le=1.0)
    classification_method: str = Field(..., description="Method used for classification")
    alternative_types: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative classifications with scores")
    keywords: List[str] = Field(default_factory=list, description="Keywords that influenced classification")
    last_classified_at: Optional[datetime] = Field(None, description="When classification was last updated")


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
    doc_type: Optional[DocType] = Field(None, description="Document type classification (legacy)")
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
    
    # Enhanced classification fields
    classification: Optional[ClassificationInfo] = Field(None, description="Enhanced document classification")
    auto_classified: bool = Field(default=False, description="Whether document was automatically classified")
    classification_reviewed: bool = Field(default=False, description="Whether classification has been manually reviewed")
    classification_reviewed_by: Optional[str] = Field(None, description="Email of person who reviewed classification")
    classification_reviewed_at: Optional[datetime] = Field(None, description="When classification was reviewed")
    
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
    
    # Team access fields for document sharing
    team_access_permission: str = Field(default="download", description="Team access level: none|view|download")
    team_can_download: bool = Field(default=False, description="Whether project team can download original file")
    gcs_copy_uri: Optional[str] = Field(None, description="GCS URI for team-accessible copy (read-only)")
    original_file_downloaded: bool = Field(default=False, description="Whether original file copied to GCS for team access")


class Document(BaseModel):
    """Complete document with metadata and content."""
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    content: Optional[str] = Field(None, description="Extracted text content")
    chunks: List[str] = Field(default_factory=list, description="Text chunks for embedding")
    vector_ids: List[str] = Field(default_factory=list, description="Vector search IDs")
