"""Admin API schemas."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .document import DocType


class AdminAction(str, Enum):
    """Admin actions."""
    APPROVE = "approve"
    REJECT = "reject"
    QUARANTINE = "quarantine"
    DELETE = "delete"


class IngestRequest(BaseModel):
    """Document ingestion request."""
    title: str = Field(..., description="Document title", min_length=1)
    doc_type: DocType = Field(..., description="Document type")
    source_uri: str = Field(..., description="Source URI (Drive, GCS, etc.)")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    owner: Optional[str] = Field(None, description="Document owner")
    version: Optional[str] = Field(None, description="Document version")


class IngestResponse(BaseModel):
    """Document ingestion response."""
    ok: bool = Field(..., description="Success status")
    job_id: Optional[str] = Field(None, description="Processing job ID")
    count: Optional[int] = Field(None, description="Number of documents processed")
    message: Optional[str] = Field(None, description="Response message")


class DriveSyncRequest(BaseModel):
    """Google Drive sync request."""
    folder_ids: List[str] = Field(..., description="Drive folder IDs to sync")
    recursive: bool = Field(default=True, description="Sync subfolders recursively")


class DriveSyncResponse(BaseModel):
    """Google Drive sync response."""
    ok: bool = Field(..., description="Success status")
    job_id: str = Field(..., description="Sync job ID")
    folders_processed: int = Field(..., description="Number of folders processed")
    files_found: int = Field(..., description="Number of files found")
