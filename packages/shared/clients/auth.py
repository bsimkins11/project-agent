"""Authentication client for Project Agent."""

import os
import jwt
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests

security = HTTPBearer()
ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN", "transparent.partners")


async def verify_google_token(token: str) -> Dict[str, Any]:
    """Verify Google OAuth ID token."""
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        )
        
        # Validate domain
        email = idinfo.get("email", "")
        if not email.endswith(f"@{ALLOWED_DOMAIN}"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to @{ALLOWED_DOMAIN} domain"
            )
        
        return {
            "email": email,
            "name": idinfo.get("name", ""),
            "picture": idinfo.get("picture", ""),
            "is_admin": email in get_admin_emails()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


def get_admin_emails() -> list:
    """Get list of admin emails from environment."""
    admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
    return [email.strip() for email in admin_emails if email.strip()]


async def require_domain_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency for domain-restricted authentication.
    
    Args:
        credentials: Bearer token from request header
        
    Returns:
        User information dict
        
    Raises:
        HTTPException: If authentication fails
    """
    return await verify_google_token(credentials.credentials)


async def require_admin_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency for admin-only authentication.
    
    Args:
        credentials: Bearer token from request header
        
    Returns:
        Admin user information dict
        
    Raises:
        HTTPException: If authentication fails or user is not admin
    """
    user = await verify_google_token(credentials.credentials)
    
    if not user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user
