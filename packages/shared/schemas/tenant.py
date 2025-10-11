"""Multi-tenancy schemas for client and project isolation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TenantContext(BaseModel):
    """Context for tenant isolation in requests."""
    user_id: str = Field(..., description="Current user ID")
    user_email: str = Field(..., description="Current user email")
    user_role: str = Field(..., description="Current user role")
    
    # Access scope
    client_ids: List[str] = Field(default_factory=list, description="Accessible client IDs")
    project_ids: List[str] = Field(default_factory=list, description="Accessible project IDs")
    
    # Current context
    active_client_id: Optional[str] = Field(None, description="Currently selected client")
    active_project_id: Optional[str] = Field(None, description="Currently selected project")
    
    def can_access_client(self, client_id: str) -> bool:
        """Check if user can access a specific client."""
        return client_id in self.client_ids or self.user_role == "super_admin"
    
    def can_access_project(self, project_id: str) -> bool:
        """Check if user can access a specific project."""
        return project_id in self.project_ids or self.user_role == "super_admin"
    
    def get_accessible_clients(self) -> List[str]:
        """Get list of accessible client IDs."""
        return self.client_ids
    
    def get_accessible_projects(self, client_id: Optional[str] = None) -> List[str]:
        """Get list of accessible project IDs, optionally filtered by client."""
        if client_id:
            # In real implementation, filter projects by client_id
            return self.project_ids
        return self.project_ids


class ClientSettings(BaseModel):
    """Client-specific settings and configuration."""
    client_id: str = Field(..., description="Client ID")
    
    # Branding
    logo_url: Optional[str] = Field(None, description="Client logo URL")
    primary_color: Optional[str] = Field(None, description="Primary brand color")
    secondary_color: Optional[str] = Field(None, description="Secondary brand color")
    
    # Features
    features_enabled: List[str] = Field(default_factory=list, description="Enabled features")
    max_documents: Optional[int] = Field(None, description="Maximum documents allowed")
    max_storage_gb: Optional[int] = Field(None, description="Maximum storage in GB")
    
    # AI Settings
    ai_enabled: bool = Field(default=True, description="Whether AI chat is enabled")
    max_ai_queries_per_day: Optional[int] = Field(None, description="Daily AI query limit")
    
    # Security
    require_2fa: bool = Field(default=False, description="Require two-factor authentication")
    allowed_ip_ranges: List[str] = Field(default_factory=list, description="Allowed IP ranges")
    session_timeout_minutes: int = Field(default=480, description="Session timeout in minutes")


class ProjectSettings(BaseModel):
    """Project-specific settings and configuration."""
    project_id: str = Field(..., description="Project ID")
    
    # Document settings
    auto_approve_documents: bool = Field(default=False, description="Auto-approve uploaded documents")
    require_metadata_validation: bool = Field(default=True, description="Require complete metadata")
    allowed_document_types: List[str] = Field(
        default_factory=lambda: ["sow", "timeline", "deliverable", "misc"],
        description="Allowed document types"
    )
    
    # AI Settings
    ai_model: str = Field(default="gemini-pro", description="AI model to use")
    max_citations: int = Field(default=5, description="Maximum citations in responses")
    
    # Workflow
    require_approval_workflow: bool = Field(default=True, description="Require document approval")
    require_permission_workflow: bool = Field(default=True, description="Require permission management")


class AuditLog(BaseModel):
    """Audit log entry for tracking all actions."""
    id: str = Field(..., description="Unique log entry ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Actor
    user_id: str = Field(..., description="User who performed the action")
    user_email: str = Field(..., description="User email")
    user_role: str = Field(..., description="User role at time of action")
    
    # Context
    client_id: Optional[str] = Field(None, description="Client context")
    project_id: Optional[str] = Field(None, description="Project context")
    
    # Action
    action_type: str = Field(..., description="Type of action (create/update/delete/view)")
    resource_type: str = Field(..., description="Resource type (document/user/project/client)")
    resource_id: str = Field(..., description="Resource ID")
    
    # Details
    action_description: str = Field(..., description="Human-readable description")
    changes: Optional[Dict[str, Any]] = Field(None, description="What changed (before/after)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    # Security
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    success: bool = Field(default=True, description="Whether action succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class DocumentAccess(BaseModel):
    """Document access record linking documents to projects and users."""
    id: str = Field(..., description="Unique access record ID")
    document_id: str = Field(..., description="Document ID")
    project_id: str = Field(..., description="Project ID")
    client_id: str = Field(..., description="Client ID")
    
    # Visibility
    visibility: str = Field(
        default="project",
        description="Visibility scope (project/client/public)"
    )
    
    # Access control
    allowed_user_ids: List[str] = Field(
        default_factory=list,
        description="Specific users who can access (empty = all project users)"
    )
    allowed_roles: List[UserRole] = Field(
        default_factory=list,
        description="Roles that can access (empty = all project users)"
    )
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(..., description="Who granted access")

