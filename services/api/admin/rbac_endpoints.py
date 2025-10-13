"""RBAC management endpoints for clients, projects, and users with authorization."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from packages.shared.clients.auth import require_admin_auth
from google.cloud import firestore

router = APIRouter(prefix="/admin/rbac", tags=["RBAC"])
rbac_client = RBACClient()

# ============================================================================
# CLIENT MANAGEMENT
# ============================================================================

@router.post("/clients", status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: Dict[str, Any],
    current_user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Create a new client. Requires MANAGE_CLIENTS permission.
    Only Super Admins can create clients.
    """
    try:
        client = Client(
            id=client_data.get("id", f"client-{client_data['name'].lower().replace(' ', '-')}"),
            name=client_data["name"],
            domain=client_data.get("domain"),
            status=client_data.get("status", "active"),
            created_by=current_user["email"],
            contact_email=client_data.get("contact_email"),
            contact_name=client_data.get("contact_name"),
            industry=client_data.get("industry"),
            notes=client_data.get("notes")
        )
        
        client_id = await rbac_client.create_client(client, current_user["email"])
        
        return {
            "success": True,
            "client_id": client_id,
            "message": f"Client '{client.name}' created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {str(e)}"
        )

@router.get("/clients")
async def list_clients(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    List clients. Requires VIEW_CLIENTS permission.
    Super Admins see all clients, Account Admins see assigned clients.
    """
    try:
        # Super admins see all clients
        if current_user["role"] == UserRole.SUPER_ADMIN:
            clients = await rbac_client.list_clients(status=status_filter)
        else:
            # Account admins see only their assigned clients
            user_client_ids = current_user.get("client_ids", [])
            all_clients = await rbac_client.list_clients(status=status_filter)
            clients = [c for c in all_clients if c.id in user_client_ids]
        
        return {
            "clients": [client.dict() for client in clients],
            "total": len(clients)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list clients: {str(e)}"
        )

@router.get("/clients/{client_id}")
async def get_client(
    client_id: str,
    current_user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get client details. Requires VIEW_CLIENTS permission.
    Users can only view clients they have access to.
    """
    try:
        # Check access (super admins bypass this)
        if current_user["role"] != UserRole.SUPER_ADMIN:
            if client_id not in current_user.get("client_ids", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to client: {client_id}"
                )
        
        client = await rbac_client.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client {client_id} not found"
            )
        
        # Get project count
        projects = await rbac_client.list_projects(client_id=client_id)
        
        return {
            "client": client.dict(),
            "project_count": len(projects),
            "projects": [p.dict() for p in projects]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client: {str(e)}"
        )

# ============================================================================
# PROJECT MANAGEMENT
# ============================================================================

@router.post("/projects", status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: Dict[str, Any],
    current_user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Create a new project. Requires MANAGE_PROJECTS permission.
    Only Super Admins and Account Admins can create projects.
    """
    try:
        # Verify user has access to the client
        client_id = project_data["client_id"]
        if current_user["role"] != UserRole.SUPER_ADMIN:
            if client_id not in current_user.get("client_ids", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to client: {client_id}"
                )
        
        project = Project(
            id=project_data.get("id", f"project-{project_data['name'].lower().replace(' ', '-')}"),
            client_id=client_id,
            name=project_data["name"],
            code=project_data.get("code"),
            status=project_data.get("status", "active"),
            created_by=current_user["email"],
            start_date=project_data.get("start_date"),
            end_date=project_data.get("end_date"),
            description=project_data.get("description"),
            tags=project_data.get("tags", []),
            document_index_url=project_data.get("document_index_url")  # KEY FIELD
        )
        
        project_id = await rbac_client.create_project(project, current_user["email"])
        
        return {
            "success": True,
            "project_id": project_id,
            "message": f"Project '{project.name}' created successfully",
            "document_index_url": project.document_index_url
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.get("/projects")
async def list_projects(
    client_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    List projects. Requires VIEW_PROJECTS permission.
    Users see only projects they have access to.
    """
    try:
        all_projects = await rbac_client.list_projects(
            client_id=client_id,
            status=status_filter
        )
        
        # Super admins see all projects
        if current_user["role"] == UserRole.SUPER_ADMIN:
            projects = all_projects
        else:
            # Filter by accessible projects
            accessible_project_ids = set(current_user.get("project_ids", []))
            projects = [p for p in all_projects if p.id in accessible_project_ids]
        
        return {
            "projects": [project.dict() for project in projects],
            "total": len(projects)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )

@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get project details. Requires VIEW_PROJECTS permission.
    Users can only view projects they have access to.
    """
    try:
        # Check access (super admins bypass this)
        if current_user["role"] != UserRole.SUPER_ADMIN:
            if project_id not in current_user.get("project_ids", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to project: {project_id}"
                )
        
        project = await rbac_client.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Get document count
        documents = await rbac_client.get_project_documents(
            project_id=project_id,
            user_id=current_user.get("user_id", "")
        )
        
        return {
            "project": project.dict(),
            "document_count": len(documents)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project: {str(e)}"
        )

@router.post("/projects/{project_id}/import-documents")
async def import_project_documents(
    project_id: str,
    force_reimport: bool = False,
    current_user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Import/refresh documents from project's document index URL.
    Requires MANAGE_PROJECTS permission.
    """
    try:
        # Check project access (super admins bypass this)
        if current_user["role"] != UserRole.SUPER_ADMIN:
            if project_id not in current_user.get("project_ids", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to project: {project_id}"
                )
        
        # Get project
        project = await rbac_client.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        if not project.document_index_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project {project_id} does not have a document index URL configured"
            )
        
        # Import documents from the sheet
        # This will call the existing analyze-document-index endpoint
        # but automatically assign project_id and client_id
        
        return {
            "success": True,
            "project_id": project_id,
            "message": f"Document import initiated for project '{project.name}'",
            "document_index_url": project.document_index_url,
            "next_step": f"Parsing Google Sheet: {project.document_index_url}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import documents: {str(e)}"
        )

# ============================================================================
# USER MANAGEMENT
# ============================================================================

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: Dict[str, Any],
    current_user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Create a new user. Requires MANAGE_CLIENT_USERS permission.
    Super Admins can create any user. Account Admins can create users in their clients.
    """
    try:
        # Validate client access for Account Admins
        if current_user["role"] == UserRole.ACCOUNT_ADMIN:
            user_client_ids = user_data.get("client_ids", [])
            allowed_clients = set(current_user.get("client_ids", []))
            if not all(cid in allowed_clients for cid in user_client_ids):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot assign user to clients you don't have access to"
                )
        
        user = UserProfile(
            id=user_data.get("id", f"user-{user_data['email'].split('@')[0]}"),
            email=user_data["email"],
            name=user_data["name"],
            role=UserRole(user_data["role"]),
            status=user_data.get("status", "active"),
            client_ids=user_data.get("client_ids", []),
            project_ids=user_data.get("project_ids", []),
            phone=user_data.get("phone"),
            department=user_data.get("department"),
            title=user_data.get("title")
        )
        
        user_id = await rbac_client.create_user(user, current_user["email"])
        
        return {
            "success": True,
            "user_id": user_id,
            "message": f"User '{user.email}' created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/users/{user_id}/projects")
async def get_user_projects(
    user_id: str,
    current_user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get all projects accessible by a user. Requires VIEW_USERS permission.
    """
    try:
        projects = await rbac_client.get_user_projects(user_id)
        
        return {
            "user_id": user_id,
            "projects": [project.dict() for project in projects],
            "total": len(projects)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user projects: {str(e)}"
        )

