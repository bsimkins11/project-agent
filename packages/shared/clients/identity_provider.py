"""Identity provider abstraction for marketplace IAM integration."""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from packages.shared.schemas.identity import (
    AuthContext,
    IdentityProvider,
    ExternalIdentity,
    LocalUserMapping,
    MarketplaceContext
)
from packages.shared.schemas.rbac import UserProfile, UserRole
from packages.shared.logging_config import get_logger
from packages.shared.exceptions import AuthenticationError

logger = get_logger(__name__)


class IIdentityProvider(ABC):
    """Abstract interface for identity providers."""
    
    @abstractmethod
    async def validate_token(self, token: str) -> AuthContext:
        """Validate authentication token and return auth context."""
        pass
    
    @abstractmethod
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from provider."""
        pass
    
    @abstractmethod
    async def sync_user(self, user_id: str) -> bool:
        """Sync user data from external provider."""
        pass


class LocalIdentityProvider(IIdentityProvider):
    """Local identity provider (current Project Agent auth)."""
    
    async def validate_token(self, token: str) -> AuthContext:
        """Validate JWT token from Project Agent."""
        # Current implementation
        from packages.shared.clients.auth import verify_google_token
        
        try:
            user_info = await verify_google_token(token)
            
            return AuthContext(
                user_id=user_info.get("email", "").replace("@", "-").replace(".", "-"),
                email=user_info["email"],
                name=user_info.get("name", ""),
                identity_provider=IdentityProvider.LOCAL,
                is_external=False,
                local_role=self._get_user_role(user_info["email"]),
                local_client_ids=[],  # TODO: Load from user profile
                local_project_ids=[]  # TODO: Load from user profile
            )
        except Exception as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")
    
    def _get_user_role(self, email: str) -> str:
        """Get user role from local database."""
        # TODO: Query Firestore for user role
        if email == "admin@transparent.partners":
            return "super_admin"
        return "end_user"
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get local user profile."""
        # TODO: Implement
        return None
    
    async def sync_user(self, user_id: str) -> bool:
        """No sync needed for local provider."""
        return True


class MarketplaceIdentityProvider(IIdentityProvider):
    """Marketplace IAM provider (future implementation)."""
    
    def __init__(self, marketplace_endpoint: str, client_id: str):
        """Initialize marketplace provider."""
        self.marketplace_endpoint = marketplace_endpoint
        self.client_id = client_id
    
    async def validate_token(self, token: str) -> AuthContext:
        """Validate token against marketplace IAM."""
        # Future implementation: Call marketplace IAM API
        logger.info("Validating token with marketplace IAM")
        
        # Example response from marketplace:
        # {
        #   "user_id": "mk-user-12345",
        #   "email": "user@company.com",
        #   "org_id": "mk-org-abc",
        #   "subscription_id": "mk-sub-xyz",
        #   "roles": ["org_admin"],
        #   "permissions": ["access_all_products"],
        #   "subscription_tier": "enterprise"
        # }
        
        raise NotImplementedError("Marketplace IAM integration not yet implemented")
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from marketplace."""
        # Future: Call marketplace API
        raise NotImplementedError("Marketplace IAM integration not yet implemented")
    
    async def sync_user(self, user_id: str) -> bool:
        """Sync user from marketplace IAM."""
        # Future: Sync user data, roles, permissions
        raise NotImplementedError("Marketplace IAM integration not yet implemented")


class IdentityProviderFactory:
    """Factory for creating identity providers."""
    
    @staticmethod
    def create_provider(
        provider_type: IdentityProvider,
        config: Optional[Dict[str, Any]] = None
    ) -> IIdentityProvider:
        """Create identity provider instance."""
        
        if provider_type == IdentityProvider.LOCAL:
            return LocalIdentityProvider()
        
        elif provider_type == IdentityProvider.MARKETPLACE:
            if not config or 'endpoint' not in config or 'client_id' not in config:
                raise ValueError("Marketplace provider requires endpoint and client_id in config")
            return MarketplaceIdentityProvider(
                marketplace_endpoint=config['endpoint'],
                client_id=config['client_id']
            )
        
        else:
            raise ValueError(f"Unsupported identity provider: {provider_type}")


# Global identity provider (configurable)
_identity_provider: Optional[IIdentityProvider] = None


def get_identity_provider() -> IIdentityProvider:
    """Get current identity provider instance."""
    global _identity_provider
    
    if _identity_provider is None:
        # Default to local provider
        from packages.shared.config import settings
        
        # Future: Read from settings which provider to use
        # For now, always use local
        _identity_provider = LocalIdentityProvider()
    
    return _identity_provider


def set_identity_provider(provider: IIdentityProvider):
    """Set global identity provider (for testing or switching providers)."""
    global _identity_provider
    _identity_provider = provider

