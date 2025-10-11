"""RBAC client for managing roles, permissions, and access control."""

from typing import List, Optional, Dict, Any
from google.cloud import firestore
from datetime import datetime

from packages.shared.schemas.rbac import (
    UserRole, 
    PermissionType, 
    Client, 
    Project, 
    UserProfile,
    UserClientAssignment,
    UserProjectAssignment,
    get_role_permissions,
    has_permission
)
from packages.shared.schemas.tenant import TenantContext, AuditLog
from packages.shared.config import settings
from packages.shared.logging_config import get_logger
from packages.shared.exceptions import AuthorizationError, DocumentNotFoundError

logger = get_logger(__name__)


class RBACClient:
    """Client for RBAC operations."""
    
    def __init__(self):
        """Initialize RBAC client."""
        self.db = firestore.Client(project=settings.gcp_project)
        self.clients_collection = "clients"
        self.projects_collection = "projects"
        self.users_collection = "users"
        self.user_client_assignments = "user_client_assignments"
        self.user_project_assignments = "user_project_assignments"
        self.audit_logs = "audit_logs"
    
    # ============================================================================
    # CLIENT MANAGEMENT
    # ============================================================================
    
    async def create_client(self, client: Client, actor_email: str) -> str:
        """Create a new client."""
        doc_ref = self.db.collection(self.clients_collection).document(client.id)
        doc_ref.set(client.dict())
        
        await self.log_action(
            user_email=actor_email,
            action_type="create",
            resource_type="client",
            resource_id=client.id,
            description=f"Created client: {client.name}"
        )
        
        logger.info(f"Created client {client.id} by {actor_email}")
        return client.id
    
    async def get_client(self, client_id: str) -> Optional[Client]:
        """Get client by ID."""
        doc = self.db.collection(self.clients_collection).document(client_id).get()
        if doc.exists:
            return Client(**doc.to_dict())
        return None
    
    async def list_clients(self, status: Optional[str] = None) -> List[Client]:
        """List all clients."""
        query = self.db.collection(self.clients_collection)
        if status:
            query = query.where("status", "==", status)
        
        docs = query.stream()
        return [Client(**doc.to_dict()) for doc in docs]
    
    # ============================================================================
    # PROJECT MANAGEMENT
    # ============================================================================
    
    async def create_project(self, project: Project, actor_email: str) -> str:
        """Create a new project."""
        doc_ref = self.db.collection(self.projects_collection).document(project.id)
        doc_ref.set(project.dict())
        
        await self.log_action(
            user_email=actor_email,
            action_type="create",
            resource_type="project",
            resource_id=project.id,
            description=f"Created project: {project.name}",
            client_id=project.client_id,
            project_id=project.id
        )
        
        logger.info(f"Created project {project.id} in client {project.client_id} by {actor_email}")
        return project.id
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        doc = self.db.collection(self.projects_collection).document(project_id).get()
        if doc.exists:
            return Project(**doc.to_dict())
        return None
    
    async def list_projects(
        self, 
        client_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Project]:
        """List projects, optionally filtered by client."""
        query = self.db.collection(self.projects_collection)
        
        if client_id:
            query = query.where("client_id", "==", client_id)
        if status:
            query = query.where("status", "==", status)
        
        docs = query.stream()
        return [Project(**doc.to_dict()) for doc in docs]
    
    # ============================================================================
    # USER MANAGEMENT
    # ============================================================================
    
    async def create_user(self, user: UserProfile, actor_email: str) -> str:
        """Create a new user."""
        doc_ref = self.db.collection(self.users_collection).document(user.id)
        doc_ref.set(user.dict())
        
        await self.log_action(
            user_email=actor_email,
            action_type="create",
            resource_type="user",
            resource_id=user.id,
            description=f"Created user: {user.email} with role {user.role.value}"
        )
        
        logger.info(f"Created user {user.email} by {actor_email}")
        return user.id
    
    async def get_user_by_email(self, email: str) -> Optional[UserProfile]:
        """Get user by email."""
        query = self.db.collection(self.users_collection).where("email", "==", email).limit(1)
        docs = list(query.stream())
        
        if docs:
            return UserProfile(**docs[0].to_dict())
        return None
    
    async def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user by ID."""
        doc = self.db.collection(self.users_collection).document(user_id).get()
        if doc.exists:
            return UserProfile(**doc.to_dict())
        return None
    
    # ============================================================================
    # ACCESS ASSIGNMENT
    # ============================================================================
    
    async def assign_user_to_client(
        self,
        user_id: str,
        client_id: str,
        role: UserRole,
        actor_email: str
    ) -> str:
        """Assign a user to a client with a specific role."""
        assignment_id = f"uca-{user_id}-{client_id}"
        assignment = UserClientAssignment(
            id=assignment_id,
            user_id=user_id,
            client_id=client_id,
            role=role,
            permissions=get_role_permissions(role),
            created_by=actor_email
        )
        
        doc_ref = self.db.collection(self.user_client_assignments).document(assignment_id)
        doc_ref.set(assignment.dict())
        
        # Update user's client_ids list
        user_ref = self.db.collection(self.users_collection).document(user_id)
        user_ref.update({
            "client_ids": firestore.ArrayUnion([client_id])
        })
        
        await self.log_action(
            user_email=actor_email,
            action_type="assign",
            resource_type="user_client_assignment",
            resource_id=assignment_id,
            description=f"Assigned user {user_id} to client {client_id} with role {role.value}",
            client_id=client_id
        )
        
        return assignment_id
    
    async def assign_user_to_project(
        self,
        user_id: str,
        project_id: str,
        role: UserRole,
        actor_email: str
    ) -> str:
        """Assign a user to a project with a specific role."""
        assignment_id = f"upa-{user_id}-{project_id}"
        assignment = UserProjectAssignment(
            id=assignment_id,
            user_id=user_id,
            project_id=project_id,
            role=role,
            permissions=get_role_permissions(role),
            created_by=actor_email
        )
        
        doc_ref = self.db.collection(self.user_project_assignments).document(assignment_id)
        doc_ref.set(assignment.dict())
        
        # Update user's project_ids list
        user_ref = self.db.collection(self.users_collection).document(user_id)
        user_ref.update({
            "project_ids": firestore.ArrayUnion([project_id])
        })
        
        await self.log_action(
            user_email=actor_email,
            action_type="assign",
            resource_type="user_project_assignment",
            resource_id=assignment_id,
            description=f"Assigned user {user_id} to project {project_id} with role {role.value}",
            project_id=project_id
        )
        
        return assignment_id
    
    # ============================================================================
    # AUTHORIZATION CHECKS
    # ============================================================================
    
    async def check_document_access(
        self,
        user_id: str,
        document_id: str,
        required_permission: PermissionType
    ) -> bool:
        """Check if user has permission to access a document."""
        # Get user
        user = await self.get_user(user_id)
        if not user:
            return False
        
        # Super admin has access to everything
        if user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Get document to find its project
        doc_ref = self.db.collection("documents").document(document_id).get()
        if not doc_ref.exists:
            return False
        
        doc_data = doc_ref.to_dict()
        project_id = doc_data.get("project_id")
        
        if not project_id:
            # Document not assigned to project - only super admin can access
            return False
        
        # Check if user has access to the project
        if project_id not in user.project_ids:
            return False
        
        # Check if user's role has the required permission
        return has_permission(user.role, required_permission)
    
    async def get_tenant_context(self, user_email: str) -> TenantContext:
        """Get tenant context for a user."""
        user = await self.get_user_by_email(user_email)
        
        if not user:
            raise AuthorizationError(f"User {user_email} not found in system")
        
        return TenantContext(
            user_id=user.id,
            user_email=user.email,
            user_role=user.role.value,
            client_ids=user.client_ids,
            project_ids=user.project_ids
        )
    
    # ============================================================================
    # AUDIT LOGGING
    # ============================================================================
    
    async def log_action(
        self,
        user_email: str,
        action_type: str,
        resource_type: str,
        resource_id: str,
        description: str,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """Log an action to audit trail."""
        user = await self.get_user_by_email(user_email)
        
        log_id = f"audit-{datetime.now().strftime('%Y%m%d%H%M%S')}-{resource_id[:8]}"
        audit_log = AuditLog(
            id=log_id,
            user_id=user.id if user else "unknown",
            user_email=user_email,
            user_role=user.role.value if user else "unknown",
            client_id=client_id,
            project_id=project_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action_description=description,
            changes=changes,
            success=success,
            error_message=error_message
        )
        
        doc_ref = self.db.collection(self.audit_logs).document(log_id)
        doc_ref.set(audit_log.dict())
        
        logger.info(f"Audit log: {action_type} {resource_type} {resource_id} by {user_email}")
        return log_id
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    async def get_user_projects(self, user_id: str) -> List[Project]:
        """Get all projects accessible by a user."""
        user = await self.get_user(user_id)
        if not user:
            return []
        
        if user.role == UserRole.SUPER_ADMIN:
            # Super admin sees all projects
            return await self.list_projects()
        
        # Get user's assigned projects
        projects = []
        for project_id in user.project_ids:
            project = await self.get_project(project_id)
            if project:
                projects.append(project)
        
        return projects
    
    async def get_user_clients(self, user_id: str) -> List[Client]:
        """Get all clients accessible by a user."""
        user = await self.get_user(user_id)
        if not user:
            return []
        
        if user.role == UserRole.SUPER_ADMIN:
            # Super admin sees all clients
            return await self.list_clients()
        
        # Get user's assigned clients
        clients = []
        for client_id in user.client_ids:
            client = await self.get_client(client_id)
            if client:
                clients.append(client)
        
        return clients
    
    async def get_project_documents(
        self,
        project_id: str,
        user_id: str,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all documents in a project (with access check)."""
        # Check user has access to project
        user = await self.get_user(user_id)
        if not user:
            raise AuthorizationError("User not found")
        
        if user.role != UserRole.SUPER_ADMIN and project_id not in user.project_ids:
            raise AuthorizationError(f"User does not have access to project {project_id}")
        
        # Query documents
        query = self.db.collection("documents").where("project_id", "==", project_id)
        
        if status_filter:
            query = query.where("status", "==", status_filter)
        
        docs = query.stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

