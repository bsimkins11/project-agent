"""Identity mapping for parent-child IAM relationship with marketplace."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MarketplaceRole(str, Enum):
    """Roles defined by marketplace/portal IAM (parent system)."""
    PLATFORM_ADMIN = "platform_admin"      # Admin across all products in marketplace
    ORG_ADMIN = "org_admin"                # Admin for their organization
    ORG_USER = "org_user"                  # Regular user in organization
    ORG_VIEWER = "org_viewer"              # Read-only user


class ProductRole(str, Enum):
    """Roles specific to Project Agent (child system)."""
    SUPER_ADMIN = "super_admin"            # Full control within Project Agent
    ACCOUNT_ADMIN = "account_admin"        # Manage client users
    PROJECT_ADMIN = "project_admin"        # Manage project documents
    END_USER = "end_user"                  # View and chat only


class RoleMapping(BaseModel):
    """Maps marketplace role to Project Agent role."""
    
    # Source (from marketplace)
    marketplace_role: MarketplaceRole = Field(..., description="Role from parent IAM")
    
    # Target (in Project Agent)
    product_role: ProductRole = Field(..., description="Mapped role in Project Agent")
    
    # Conditions
    requires_explicit_assignment: bool = Field(
        default=False,
        description="If true, requires explicit client/project assignment"
    )
    auto_grant_all_projects: bool = Field(
        default=False,
        description="If true, auto-grant access to all projects in org"
    )


# Default role mapping from marketplace to Project Agent
DEFAULT_ROLE_MAPPING: Dict[MarketplaceRole, ProductRole] = {
    MarketplaceRole.PLATFORM_ADMIN: ProductRole.SUPER_ADMIN,
    MarketplaceRole.ORG_ADMIN: ProductRole.ACCOUNT_ADMIN,
    MarketplaceRole.ORG_USER: ProductRole.END_USER,
    MarketplaceRole.ORG_VIEWER: ProductRole.END_USER,
}


class MarketplaceUserContext(BaseModel):
    """User context received from marketplace/portal IAM."""
    
    # Identity (provided by marketplace)
    marketplace_user_id: str = Field(..., description="User ID in marketplace")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User full name")
    
    # Organization (provided by marketplace)
    marketplace_org_id: str = Field(..., description="Organization ID in marketplace")
    org_name: str = Field(..., description="Organization name")
    
    # Role (provided by marketplace - THIS IS THE SOURCE OF TRUTH)
    marketplace_role: MarketplaceRole = Field(..., description="Role assigned by marketplace")
    
    # Product access (provided by marketplace)
    has_project_agent_access: bool = Field(..., description="Whether user can access Project Agent")
    subscription_tier: Optional[str] = Field(None, description="Subscription tier")
    
    # Token
    token: str = Field(..., description="JWT token from marketplace")
    issued_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(None, description="Token expiration")


class ProjectAgentUserContext(BaseModel):
    """User context within Project Agent (child system)."""
    
    # Local identity
    local_user_id: str = Field(..., description="User ID in Project Agent")
    
    # Reference to parent
    marketplace_user_id: Optional[str] = Field(None, description="User ID in marketplace (if federated)")
    is_federated: bool = Field(default=False, description="Whether user comes from marketplace")
    
    # Role (derived from marketplace OR set locally)
    product_role: ProductRole = Field(..., description="Role in Project Agent")
    role_source: str = Field(
        default="marketplace",
        description="Where role comes from: marketplace|local|manual"
    )
    
    # Product-specific access
    client_ids: List[str] = Field(default_factory=list, description="Accessible clients")
    project_ids: List[str] = Field(default_factory=list, description="Accessible projects")
    
    # Original marketplace context (if federated)
    marketplace_context: Optional[MarketplaceUserContext] = Field(
        None,
        description="Original context from marketplace"
    )
    
    # Permissions
    permissions: List[str] = Field(default_factory=list, description="Computed permissions")
    
    def get_effective_role(self) -> ProductRole:
        """Get effective role, preferring marketplace role if federated."""
        return self.product_role
    
    def can_access_project(self, project_id: str) -> bool:
        """Check if user can access a project."""
        if self.product_role == ProductRole.SUPER_ADMIN:
            return True
        return project_id in self.project_ids


def map_marketplace_to_product_role(marketplace_role: MarketplaceRole) -> ProductRole:
    """
    Map marketplace role to Project Agent role.
    
    Marketplace determines the role, we just map it to our product-specific equivalent.
    """
    return DEFAULT_ROLE_MAPPING.get(marketplace_role, ProductRole.END_USER)


def create_project_agent_context(
    marketplace_context: MarketplaceUserContext,
    local_user_id: str,
    client_ids: List[str],
    project_ids: List[str]
) -> ProjectAgentUserContext:
    """
    Create Project Agent context from marketplace context.
    
    This is called when a federated user accesses Project Agent.
    """
    # Map marketplace role to product role
    product_role = map_marketplace_to_product_role(marketplace_context.marketplace_role)
    
    # For platform admins, auto-grant access to everything
    auto_grant_all = (marketplace_context.marketplace_role == MarketplaceRole.PLATFORM_ADMIN)
    
    return ProjectAgentUserContext(
        local_user_id=local_user_id,
        marketplace_user_id=marketplace_context.marketplace_user_id,
        is_federated=True,
        product_role=product_role,
        role_source="marketplace",  # Role came from marketplace
        client_ids=client_ids if not auto_grant_all else [],  # Empty = all access for super admin
        project_ids=project_ids if not auto_grant_all else [],
        marketplace_context=marketplace_context,
        permissions=[]  # TODO: Compute based on role
    )


class ChildIAMInterface(BaseModel):
    """
    Interface that Project Agent exposes to parent marketplace IAM.
    
    This defines what the marketplace can tell us about users.
    """
    
    # What marketplace sends to Project Agent
    user_id: str = Field(..., description="Marketplace user ID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    org_id: str = Field(..., description="Organization ID")
    role: str = Field(..., description="Role in marketplace (platform_admin|org_admin|org_user|org_viewer)")
    
    # Product-specific context (marketplace may send this)
    product_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Product-specific metadata from marketplace"
    )
    
    # What Project Agent does with it
    def to_marketplace_context(self) -> MarketplaceUserContext:
        """Convert to marketplace context."""
        return MarketplaceUserContext(
            marketplace_user_id=self.user_id,
            email=self.email,
            name=self.name,
            marketplace_org_id=self.org_id,
            org_name=self.product_context.get('org_name', '') if self.product_context else '',
            marketplace_role=MarketplaceRole(self.role),
            has_project_agent_access=True,  # If they got here, they have access
            token="",  # Populated by auth system
        )


# Example configuration for production
MARKETPLACE_IAM_CONFIG = {
    "enabled": False,  # Set to True when marketplace is ready
    "endpoint": "https://marketplace-iam.example.com/api/v1",
    "validate_token_endpoint": "/auth/validate",
    "get_user_endpoint": "/users/{user_id}",
    "webhook_secret": "configured-in-env",
    
    # Role mapping
    "role_mapping": {
        "platform_admin": "super_admin",
        "org_admin": "account_admin",
        "org_user": "end_user",
        "org_viewer": "end_user"
    },
    
    # Auto-provisioning
    "auto_provision_users": True,
    "default_role": "end_user",
    
    # Sync settings
    "sync_interval_hours": 24,
    "sync_on_login": True
}

