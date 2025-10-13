"""Authentication client for Project Agent - POC version, portal-ready."""

import os
import jwt
import logging
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google.auth.transport import requests

logger = logging.getLogger(__name__)

security = HTTPBearer()
ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN", "transparent.partners")

# POC Configuration - Single client/project for testing
# In portal integration, these will come from JWT claims
POC_CLIENT_ID = os.getenv("POC_CLIENT_ID", "transparent-partners")
POC_PROJECT_ID = os.getenv("POC_PROJECT_ID", "tp-main-project")


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


async def get_user_oauth_credentials(access_token: Optional[str]) -> Optional[Credentials]:
    """
    Extract OAuth credentials from user's access token.
    
    This allows the system to access Google Drive/Sheets on behalf of the user,
    using their own permissions (no manual sharing required).
    
    Security benefits:
    - User-scoped access (principle of least privilege)
    - Token expiration (~1 hour)
    - Clear audit trail (actions attributed to user)
    - Revocable (user can revoke via Google account)
    
    Args:
        access_token: User's OAuth access token with Drive/Sheets scopes
        
    Returns:
        Credentials object if valid, None if not available or invalid
    """
    if not access_token:
        logger.debug("No access token provided for OAuth credentials")
        return None
    
    try:
        # Create credentials from the access token
        # The token should have these scopes:
        # - https://www.googleapis.com/auth/drive.readonly
        # - https://www.googleapis.com/auth/spreadsheets.readonly
        credentials = Credentials(token=access_token)
        
        logger.info("Successfully created OAuth credentials from access token")
        return credentials
        
    except Exception as e:
        logger.warning(f"Could not create OAuth credentials: {e}")
        return None


async def require_domain_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency for domain-restricted authentication.
    
    Returns user info with POC client/project context.
    Portal integration: Will extract client_ids/project_ids from JWT claims.
    
    Args:
        credentials: Bearer token from request header
        
    Returns:
        User information dict with access context
    """
    user_info = await verify_google_token(credentials.credentials)
    
    # POC: Assign single client/project to all users
    # Portal integration: Extract from JWT claims
    user_info["client_ids"] = [POC_CLIENT_ID]
    user_info["project_ids"] = [POC_PROJECT_ID]
    user_info["client_id"] = POC_CLIENT_ID  # Active context
    user_info["project_id"] = POC_PROJECT_ID  # Active context
    
    return user_info


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
        HTTPException: If user is not an admin
    """
    user = await require_domain_auth(credentials)
    
    if not user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


def get_poc_context() -> Dict[str, Any]:
    """
    Get POC client/project context.
    
    For POC: Returns hardcoded single client/project.
    Portal integration: Will be replaced by portal JWT claims.
    
    Returns:
        Dict with client_id and project_id
    """
    return {
        "client_id": POC_CLIENT_ID,
        "project_id": POC_PROJECT_ID,
        "client_ids": [POC_CLIENT_ID],
        "project_ids": [POC_PROJECT_ID]
    }


def filter_documents_by_access(user_email: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter documents based on user's access.
    
    POC: All authenticated users get full access to all documents.
    Portal integration: Will filter by user's actual client_ids/project_ids from JWT.
    
    Args:
        user_email: User's email address
        documents: List of document dictionaries
        
    Returns:
        Filtered list of documents user can access
    """
    # POC: Grant full access to all documents
    # Portal integration: Add filtering logic here based on JWT claims
    return documents


def check_document_access(user_email: str, doc_id: str) -> bool:
    """
    Check if user can access a specific document.
    
    POC: All authenticated users can access all documents.
    Portal integration: Will check against user's client_ids/project_ids from JWT.
    
    Args:
        user_email: User's email address
        doc_id: Document ID to check
        
    Returns:
        True if user can access document
    """
    # POC: Grant full access
    # Portal integration: Add check logic here based on JWT claims
    return True


# Portal Integration Contract
"""
PORTAL INTEGRATION NOTES:

When integrating with the portal, the portal should provide JWT tokens with these claims:

{
    "email": "user@transparent.partners",
    "name": "User Name",
    "client_ids": ["client-1", "client-2"],  # User's assigned clients
    "project_ids": ["proj-1", "proj-2"],      # User's assigned projects
    "role": "project_admin",                   # User's role (for UI display)
    "permissions": ["view_documents", "chat"]  # Optional: explicit permissions
}

The auth middleware will extract these claims and make them available to all endpoints.
Data filtering will automatically use client_ids/project_ids to restrict queries.

Migration Steps:
1. Update verify_google_token() to decode portal JWT instead of Google OAuth
2. Extract client_ids, project_ids, role from JWT claims
3. Update filter_documents_by_access() to use user's actual client_ids/project_ids
4. No changes needed to API endpoints - they already use the user context
"""
