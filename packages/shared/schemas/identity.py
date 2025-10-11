"""Identity abstraction layer for marketplace-level IAM integration."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class IdentityProvider(str, Enum):
    """Identity provider types."""
    LOCAL = "local"                    # Project Agent local auth (current)
    MARKETPLACE = "marketplace"        # Future marketplace IAM
    GOOGLE = "google"                  # Google Workspace SSO
    AZURE_AD = "azure_ad"             # Microsoft Azure AD
    OKTA = "okta"                     # Okta SSO
    CUSTOM = "custom"                 # Custom enterprise SSO


class ExternalIdentity(BaseModel):
    """Reference to user identity in external IAM system."""
    
    # External identity
    external_user_id: str = Field(..., description="User ID in external system")
    external_email: str = Field(..., description="Email in external system")
    identity_provider: IdentityProvider = Field(..., description="Which IAM system this user comes from")
    
    # Provider-specific metadata
    provider_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Provider-specific user data (roles, groups, etc.)"
    )
    
    # Synchronization
    last_synced: Optional[datetime] = Field(None, description="Last sync with external IAM")
    sync_enabled: bool = Field(default=True, description="Whether to sync with external IAM")
    
    # Federation
    federated_at: datetime = Field(default_factory=datetime.now)
    federation_status: str = Field(default="active", description="active|suspended|revoked")


class LocalUserMapping(BaseModel):
    """Maps external user to Project Agent local user."""
    
    # Local identity (Project Agent)
    local_user_id: str = Field(..., description="User ID in Project Agent")
    local_email: str = Field(..., description="Email in Project Agent")
    
    # External identity
    external_identity: ExternalIdentity = Field(..., description="Reference to external IAM")
    
    # Mapping metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(..., description="Who created this mapping")
    
    # Sync configuration
    auto_provision: bool = Field(
        default=True,
        description="Auto-create local user on first login from external IAM"
    )
    inherit_external_roles: bool = Field(
        default=False,
        description="Whether to inherit roles from external IAM"
    )


class MarketplaceContext(BaseModel):
    """Context from marketplace-level IAM (future)."""
    
    # Marketplace identifiers
    marketplace_user_id: str = Field(..., description="User ID in marketplace")
    marketplace_org_id: str = Field(..., description="Organization ID in marketplace")
    marketplace_subscription_id: Optional[str] = Field(None, description="Subscription ID")
    
    # Marketplace permissions
    marketplace_roles: list[str] = Field(default_factory=list, description="Roles in marketplace")
    marketplace_permissions: list[str] = Field(default_factory=list, description="Global permissions")
    
    # Product access
    product_access: Dict[str, Any] = Field(
        default_factory=dict,
        description="Access levels for different products"
    )
    
    # Billing context
    subscription_tier: Optional[str] = Field(None, description="Subscription tier (free/pro/enterprise)")
    quota_limits: Optional[Dict[str, int]] = Field(None, description="Usage quotas")


class AuthContext(BaseModel):
    """Unified auth context supporting both local and marketplace IAM."""
    
    # Core identity
    user_id: str = Field(..., description="User ID (local or external)")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User display name")
    
    # Identity source
    identity_provider: IdentityProvider = Field(..., description="Where this identity comes from")
    is_external: bool = Field(default=False, description="Whether from external IAM")
    
    # Project Agent context (local)
    local_role: Optional[str] = Field(None, description="Role in Project Agent")
    local_client_ids: list[str] = Field(default_factory=list, description="Accessible clients")
    local_project_ids: list[str] = Field(default_factory=list, description="Accessible projects")
    
    # Marketplace context (future)
    marketplace_context: Optional[MarketplaceContext] = Field(
        None,
        description="Context from marketplace IAM (if applicable)"
    )
    
    # Session
    session_id: Optional[str] = Field(None, description="Session identifier")
    issued_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(None, description="Token expiration")
    
    def is_from_marketplace(self) -> bool:
        """Check if user is from marketplace IAM."""
        return self.identity_provider == IdentityProvider.MARKETPLACE
    
    def get_effective_role(self) -> str:
        """Get effective role considering both local and marketplace."""
        # Future: Combine local role with marketplace permissions
        return self.local_role or "end_user"
    
    def has_marketplace_permission(self, permission: str) -> bool:
        """Check if user has a marketplace-level permission."""
        if not self.marketplace_context:
            return False
        return permission in self.marketplace_context.marketplace_permissions


class IAMConfig(BaseModel):
    """Configuration for IAM integration."""
    
    # Current provider
    primary_identity_provider: IdentityProvider = Field(
        default=IdentityProvider.LOCAL,
        description="Primary identity provider"
    )
    
    # Federation settings
    enable_marketplace_federation: bool = Field(
        default=False,
        description="Enable marketplace IAM federation"
    )
    marketplace_iam_endpoint: Optional[str] = Field(
        None,
        description="Marketplace IAM API endpoint"
    )
    marketplace_client_id: Optional[str] = Field(
        None,
        description="Client ID for marketplace integration"
    )
    
    # SSO settings
    enable_sso: bool = Field(default=False, description="Enable SSO")
    sso_provider: Optional[IdentityProvider] = Field(None, description="SSO provider")
    sso_metadata_url: Optional[str] = Field(None, description="SSO metadata URL")
    
    # Auto-provisioning
    auto_provision_users: bool = Field(
        default=True,
        description="Auto-create users on first login from external IAM"
    )
    default_role_for_new_users: str = Field(
        default="end_user",
        description="Default role for auto-provisioned users"
    )

