"""Role-Based Access Control (RBAC) schemas for multi-tenant system."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class UserRole(str, Enum):
    """User role types in the system."""
    SUPER_ADMIN = "super_admin"          # Full system access
    ACCOUNT_ADMIN = "account_admin"      # Manage users within clients
    PROJECT_ADMIN = "project_admin"      # Manage documents within projects
    END_USER = "end_user"                # View-only access to assigned projects


class PermissionType(str, Enum):
    """Permission types for granular access control."""
    # System-level permissions
    MANAGE_CLIENTS = "manage_clients"
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    
    # Client-level permissions
    VIEW_CLIENT = "view_client"
    MANAGE_PROJECTS = "manage_projects"
    
    # Project-level permissions
    VIEW_PROJECT = "view_project"
    MANAGE_DOCUMENTS = "manage_documents"
    UPLOAD_DOCUMENTS = "upload_documents"
    APPROVE_DOCUMENTS = "approve_documents"
    DELETE_DOCUMENTS = "delete_documents"
    
    # Document-level permissions
    VIEW_DOCUMENTS = "view_documents"
    CHAT_WITH_DOCUMENTS = "chat_with_documents"
    DOWNLOAD_DOCUMENTS = "download_documents"


class Client(BaseModel):
    """Client/Organization entity."""
    id: str = Field(..., description="Unique client identifier")
    name: str = Field(..., description="Client organization name")
    domain: Optional[str] = Field(None, description="Email domain for automatic assignment")
    status: str = Field(default="active", description="Client status (active/inactive)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(..., description="Email of creator")
    
    # Metadata
    contact_email: Optional[EmailStr] = Field(None, description="Primary contact email")
    contact_name: Optional[str] = Field(None, description="Primary contact name")
    industry: Optional[str] = Field(None, description="Client industry")
    notes: Optional[str] = Field(None, description="Additional notes")


class Project(BaseModel):
    """Project entity within a client."""
    id: str = Field(..., description="Unique project identifier")
    client_id: str = Field(..., description="Parent client ID")
    name: str = Field(..., description="Project name")
    code: Optional[str] = Field(None, description="Project code/abbreviation")
    status: str = Field(default="active", description="Project status (active/archived/completed)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(..., description="Email of creator")
    
    # Project metadata
    start_date: Optional[datetime] = Field(None, description="Project start date")
    end_date: Optional[datetime] = Field(None, description="Project end date")
    description: Optional[str] = Field(None, description="Project description")
    tags: List[str] = Field(default_factory=list, description="Project tags")
    
    # Document index
    document_index_url: Optional[str] = Field(None, description="Google Sheets index URL")
    document_count: int = Field(default=0, description="Number of documents in project")


class UserProfile(BaseModel):
    """User profile with role and access assignments."""
    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    role: UserRole = Field(..., description="User role")
    status: str = Field(default="active", description="User status (active/inactive/suspended)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Access assignments
    client_ids: List[str] = Field(default_factory=list, description="Assigned client IDs")
    project_ids: List[str] = Field(default_factory=list, description="Assigned project IDs")
    
    # Metadata
    phone: Optional[str] = Field(None, description="Phone number")
    department: Optional[str] = Field(None, description="Department")
    title: Optional[str] = Field(None, description="Job title")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class UserClientAssignment(BaseModel):
    """Assignment of user to client with specific permissions."""
    id: str = Field(..., description="Unique assignment identifier")
    user_id: str = Field(..., description="User ID")
    client_id: str = Field(..., description="Client ID")
    role: UserRole = Field(..., description="User's role within this client")
    permissions: List[PermissionType] = Field(default_factory=list, description="Specific permissions")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(..., description="Who created this assignment")


class UserProjectAssignment(BaseModel):
    """Assignment of user to project with specific permissions."""
    id: str = Field(..., description="Unique assignment identifier")
    user_id: str = Field(..., description="User ID")
    project_id: str = Field(..., description="Project ID")
    role: UserRole = Field(..., description="User's role within this project")
    permissions: List[PermissionType] = Field(default_factory=list, description="Specific permissions")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(..., description="Who created this assignment")


class AccessRequest(BaseModel):
    """User request for access to client or project."""
    id: str = Field(..., description="Unique request identifier")
    user_id: str = Field(..., description="Requesting user ID")
    user_email: EmailStr = Field(..., description="Requesting user email")
    
    # What they're requesting
    client_id: Optional[str] = Field(None, description="Client ID (if requesting client access)")
    project_id: Optional[str] = Field(None, description="Project ID (if requesting project access)")
    requested_role: UserRole = Field(..., description="Requested role")
    
    # Request details
    reason: Optional[str] = Field(None, description="Reason for access request")
    status: str = Field(default="pending", description="Request status (pending/approved/denied)")
    
    # Tracking
    requested_at: datetime = Field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = Field(None, description="When request was reviewed")
    reviewed_by: Optional[str] = Field(None, description="Who reviewed the request")
    review_notes: Optional[str] = Field(None, description="Review notes/reason")


# Permission mapping by role
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: [
        PermissionType.MANAGE_CLIENTS,
        PermissionType.MANAGE_USERS,
        PermissionType.MANAGE_SYSTEM,
        PermissionType.VIEW_CLIENT,
        PermissionType.MANAGE_PROJECTS,
        PermissionType.VIEW_PROJECT,
        PermissionType.MANAGE_DOCUMENTS,
        PermissionType.UPLOAD_DOCUMENTS,
        PermissionType.APPROVE_DOCUMENTS,
        PermissionType.DELETE_DOCUMENTS,
        PermissionType.VIEW_DOCUMENTS,
        PermissionType.CHAT_WITH_DOCUMENTS,
        PermissionType.DOWNLOAD_DOCUMENTS,
    ],
    UserRole.ACCOUNT_ADMIN: [
        PermissionType.VIEW_CLIENT,
        PermissionType.MANAGE_USERS,  # Within their client only
        PermissionType.MANAGE_PROJECTS,  # Within their client only
        PermissionType.VIEW_PROJECT,
        PermissionType.VIEW_DOCUMENTS,
        PermissionType.CHAT_WITH_DOCUMENTS,
    ],
    UserRole.PROJECT_ADMIN: [
        PermissionType.VIEW_PROJECT,
        PermissionType.MANAGE_DOCUMENTS,  # Within their project only
        PermissionType.UPLOAD_DOCUMENTS,
        PermissionType.APPROVE_DOCUMENTS,
        PermissionType.DELETE_DOCUMENTS,
        PermissionType.VIEW_DOCUMENTS,
        PermissionType.CHAT_WITH_DOCUMENTS,
        PermissionType.DOWNLOAD_DOCUMENTS,
    ],
    UserRole.END_USER: [
        PermissionType.VIEW_PROJECT,
        PermissionType.VIEW_DOCUMENTS,
        PermissionType.CHAT_WITH_DOCUMENTS,
    ],
}


def get_role_permissions(role: UserRole) -> List[PermissionType]:
    """Get all permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(user_role: UserRole, required_permission: PermissionType) -> bool:
    """Check if a role has a specific permission."""
    return required_permission in ROLE_PERMISSIONS.get(user_role, [])

