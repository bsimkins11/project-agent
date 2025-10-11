"""Authentication and Authorization client for Project Agent with RBAC support."""

import os
import jwt
from typing import Dict, Any, Optional, List, Callable
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests
from functools import wraps

from packages.shared.schemas.rbac import UserRole, PermissionType, get_role_permissions, has_permission
from packages.shared.clients.rbac import RBACClient

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


# ============================================================================
# RBAC AUTHORIZATION MIDDLEWARE (Phase 3)
# ============================================================================

_rbac_client = None

def get_rbac_client() -> RBACClient:
    """Get or create RBAC client singleton."""
    global _rbac_client
    if _rbac_client is None:
        _rbac_client = RBACClient()
    return _rbac_client


async def get_user_context(user_email: str) -> Dict[str, Any]:
    """
    Get full user context including role, permissions, and access.
    
    Args:
        user_email: User email address
        
    Returns:
        User context dict with role, permissions, clients, projects
    """
    rbac = get_rbac_client()
    
    try:
        # Get user profile
        user = await rbac.get_user_by_email(user_email)
        if not user:
            # Return basic context for users not in RBAC system
            return {
                "email": user_email,
                "role": UserRole.END_USER,
                "permissions": [],
                "client_ids": [],
                "project_ids": []
            }
        
        # Get role permissions
        permissions = get_role_permissions(user.role)
        
        # Get client assignments
        client_ids = await rbac.get_user_clients(user.id)
        
        # Get project assignments
        project_ids = await rbac.get_user_projects(user.id)
        
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "permissions": permissions,
            "client_ids": client_ids,
            "project_ids": project_ids,
            "status": user.status
        }
    except Exception as e:
        # Fallback for errors
        return {
            "email": user_email,
            "role": UserRole.END_USER,
            "permissions": [],
            "client_ids": [],
            "project_ids": []
        }


def require_permission(permission: PermissionType):
    """
    Decorator/dependency to require specific permission.
    
    Usage:
        @app.get("/admin/clients")
        async def get_clients(user: dict = Depends(require_permission(PermissionType.MANAGE_CLIENTS))):
            ...
    
    Args:
        permission: Required permission
        
    Returns:
        FastAPI dependency that checks permission
    """
    async def permission_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        # First authenticate
        user = await verify_google_token(credentials.credentials)
        
        # Get user context with RBAC
        context = await get_user_context(user["email"])
        
        # Check permission
        if permission not in context["permissions"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}"
            )
        
        # Return enriched user context
        return {**user, **context}
    
    return permission_checker


def require_role(min_role: UserRole):
    """
    Decorator/dependency to require minimum role level.
    
    Role hierarchy: super_admin > account_admin > project_admin > end_user
    
    Usage:
        @app.post("/admin/projects")
        async def create_project(user: dict = Depends(require_role(UserRole.ACCOUNT_ADMIN))):
            ...
    
    Args:
        min_role: Minimum required role
        
    Returns:
        FastAPI dependency that checks role
    """
    role_hierarchy = {
        UserRole.SUPER_ADMIN: 4,
        UserRole.ACCOUNT_ADMIN: 3,
        UserRole.PROJECT_ADMIN: 2,
        UserRole.END_USER: 1
    }
    
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        # First authenticate
        user = await verify_google_token(credentials.credentials)
        
        # Get user context with RBAC
        context = await get_user_context(user["email"])
        
        # Check role level
        user_role_level = role_hierarchy.get(context["role"], 0)
        required_role_level = role_hierarchy.get(min_role, 0)
        
        if user_role_level < required_role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {min_role.value} or higher"
            )
        
        # Return enriched user context
        return {**user, **context}
    
    return role_checker


def require_client_access(client_id_param: str = "client_id"):
    """
    Decorator/dependency to require access to specific client.
    
    Usage:
        @app.get("/clients/{client_id}/projects")
        async def get_projects(
            client_id: str,
            user: dict = Depends(require_client_access())
        ):
            ...
    
    Args:
        client_id_param: Name of path parameter containing client_id
        
    Returns:
        FastAPI dependency that checks client access
    """
    async def client_access_checker(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        # First authenticate
        user = await verify_google_token(credentials.credentials)
        
        # Get user context with RBAC
        context = await get_user_context(user["email"])
        
        # Super admins have access to all clients
        if context["role"] == UserRole.SUPER_ADMIN:
            return {**user, **context}
        
        # Get client_id from path parameters
        client_id = request.path_params.get(client_id_param)
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Client ID required in path parameter: {client_id_param}"
            )
        
        # Check if user has access to this client
        if client_id not in context["client_ids"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to client: {client_id}"
            )
        
        # Return enriched user context
        return {**user, **context}
    
    return client_access_checker


def require_project_access(project_id_param: str = "project_id"):
    """
    Decorator/dependency to require access to specific project.
    
    Usage:
        @app.get("/projects/{project_id}/documents")
        async def get_documents(
            project_id: str,
            user: dict = Depends(require_project_access())
        ):
            ...
    
    Args:
        project_id_param: Name of path parameter containing project_id
        
    Returns:
        FastAPI dependency that checks project access
    """
    async def project_access_checker(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        # First authenticate
        user = await verify_google_token(credentials.credentials)
        
        # Get user context with RBAC
        context = await get_user_context(user["email"])
        
        # Super admins have access to all projects
        if context["role"] == UserRole.SUPER_ADMIN:
            return {**user, **context}
        
        # Get project_id from path parameters
        project_id = request.path_params.get(project_id_param)
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project ID required in path parameter: {project_id_param}"
            )
        
        # Check if user has access to this project
        if project_id not in context["project_ids"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to project: {project_id}"
            )
        
        # Return enriched user context
        return {**user, **context}
    
    return project_access_checker


async def filter_documents_by_access(
    user_email: str,
    documents: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Filter documents based on user's project/client access.
    
    Args:
        user_email: User email address
        documents: List of document dicts
        
    Returns:
        Filtered list of documents user can access
    """
    context = await get_user_context(user_email)
    
    # Super admins see everything
    if context["role"] == UserRole.SUPER_ADMIN:
        return documents
    
    # Filter by accessible projects
    accessible_projects = set(context["project_ids"])
    accessible_clients = set(context["client_ids"])
    
    filtered = []
    for doc in documents:
        # Check project access
        if doc.get("project_id") in accessible_projects:
            filtered.append(doc)
            continue
        
        # Check client access (if no project_id or user has client-level access)
        if doc.get("client_id") in accessible_clients:
            filtered.append(doc)
            continue
    
    return filtered


async def check_document_access(
    user_email: str,
    doc_id: str
) -> bool:
    """
    Check if user has access to a specific document.
    
    Args:
        user_email: User email address
        doc_id: Document ID
        
    Returns:
        True if user can access document
    """
    rbac = get_rbac_client()
    context = await get_user_context(user_email)
    
    # Super admins have access to everything
    if context["role"] == UserRole.SUPER_ADMIN:
        return True
    
    # Get document to check its project/client
    from packages.shared.clients.firestore import FirestoreClient
    firestore = FirestoreClient()
    
    try:
        doc = await firestore.get_document(doc_id)
        if not doc:
            return False
        
        # Check project access
        if doc.get("project_id") in context["project_ids"]:
            return True
        
        # Check client access
        if doc.get("client_id") in context["client_ids"]:
            return True
        
        return False
    except Exception:
        return False
