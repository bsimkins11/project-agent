# Multi-Tenant RBAC Implementation Plan

## 🎯 Overview

Transform Project Agent from single-tenant to multi-tenant SaaS with sophisticated role-based access control.

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SUPER ADMIN                                 │
│  • Manages all clients, projects, users                         │
│  • Full system access                                            │
│  • System configuration                                          │
└─────────────────┬───────────────────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┬─────────────────┐
    ▼                           ▼                 ▼
┌─────────────┐         ┌─────────────┐   ┌─────────────┐
│  CLIENT A   │         │  CLIENT B   │   │  CLIENT C   │
│  (Acme Inc) │         │  (XYZ Corp) │   │  (ABC Ltd)  │
└──────┬──────┘         └──────┬──────┘   └──────┬──────┘
       │                       │                  │
   ┌───┴───┐              ┌────┴────┐        ┌───┴────┐
   ▼       ▼              ▼         ▼        ▼        ▼
┌────┐  ┌────┐        ┌────┐   ┌────┐   ┌────┐  ┌────┐
│Proj│  │Proj│        │Proj│   │Proj│   │Proj│  │Proj│
│ 1  │  │ 2  │        │ 3  │   │ 4  │   │ 5  │  │ 6  │
└──┬─┘  └──┬─┘        └──┬─┘   └──┬─┘   └──┬─┘  └──┬─┘
   │       │             │        │        │       │
   ▼       ▼             ▼        ▼        ▼       ▼
 Docs    Docs          Docs     Docs     Docs    Docs
```

### **User Roles & Access:**

```
┌────────────────────────────────────────────────────────┐
│  ACCOUNT ADMIN                                          │
│  Client: Acme Inc                                       │
│  ├─ Can manage users within Acme Inc                   │
│  ├─ Can view all projects in Acme Inc                  │
│  └─ Can assign users to Project 1 & 2                  │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  PROJECT ADMIN                                          │
│  Project: Project 1                                     │
│  ├─ Can upload documents to Project 1                  │
│  ├─ Can approve/reject documents in Project 1          │
│  └─ Can manage document metadata in Project 1          │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  END USER                                               │
│  Projects: Project 1, Project 3                         │
│  ├─ Can view approved documents in Project 1 & 3       │
│  ├─ Can chat with AI about Project 1 & 3 documents    │
│  └─ No admin capabilities                              │
└────────────────────────────────────────────────────────┘
```

---

## 🗃️ Database Schema

### **Collections:**

```
firestore/
├── clients/
│   └── {client_id}
│       ├── id: string
│       ├── name: string
│       ├── domain: string
│       ├── status: active|inactive
│       └── created_at: timestamp
│
├── projects/
│   └── {project_id}
│       ├── id: string
│       ├── client_id: string (reference)
│       ├── name: string
│       ├── code: string
│       ├── status: active|archived|completed
│       ├── document_index_url: string
│       └── created_at: timestamp
│
├── users/
│   └── {user_id}
│       ├── id: string
│       ├── email: string
│       ├── name: string
│       ├── role: super_admin|account_admin|project_admin|end_user
│       ├── client_ids: array<string>
│       ├── project_ids: array<string>
│       └── status: active|inactive|suspended
│
├── user_client_assignments/
│   └── {assignment_id}
│       ├── user_id: string
│       ├── client_id: string
│       ├── role: UserRole
│       └── permissions: array<PermissionType>
│
├── user_project_assignments/
│   └── {assignment_id}
│       ├── user_id: string
│       ├── project_id: string
│       ├── role: UserRole
│       └── permissions: array<PermissionType>
│
├── documents/ (ENHANCED)
│   └── {doc_id}
│       ├── ... existing fields ...
│       ├── client_id: string (NEW)
│       ├── project_id: string (NEW)
│       └── visibility: project|client|public (NEW)
│
└── audit_logs/
    └── {log_id}
        ├── timestamp: timestamp
        ├── user_email: string
        ├── action_type: create|update|delete|view
        ├── resource_type: string
        ├── resource_id: string
        └── success: boolean
```

---

## 🔐 Permission Matrix

| Action | Super Admin | Account Admin | Project Admin | End User |
|--------|-------------|---------------|---------------|----------|
| **System Management** |
| Manage all clients | ✅ | ❌ | ❌ | ❌ |
| View system logs | ✅ | ❌ | ❌ | ❌ |
| System configuration | ✅ | ❌ | ❌ | ❌ |
| **Client Management** |
| Create clients | ✅ | ❌ | ❌ | ❌ |
| View assigned clients | ✅ | ✅ | ❌ | ❌ |
| Manage client settings | ✅ | ✅ | ❌ | ❌ |
| **Project Management** |
| Create projects | ✅ | ✅ | ❌ | ❌ |
| View assigned projects | ✅ | ✅ | ✅ | ✅ |
| Archive projects | ✅ | ✅ | ❌ | ❌ |
| **User Management** |
| Create users (any client) | ✅ | ❌ | ❌ | ❌ |
| Create users (own client) | ✅ | ✅ | ❌ | ❌ |
| Assign to projects | ✅ | ✅ | ❌ | ❌ |
| **Document Management** |
| Upload documents | ✅ | ❌ | ✅ | ❌ |
| Approve documents | ✅ | ❌ | ✅ | ❌ |
| Delete documents | ✅ | ❌ | ✅ | ❌ |
| View documents | ✅ | ✅ | ✅ | ✅ |
| **AI Chat** |
| Chat with AI | ✅ | ✅ | ✅ | ✅ |
| View citations | ✅ | ✅ | ✅ | ✅ |

---

## 🛠️ Implementation Phases

### **Phase 1: Data Model (Week 1)**
- [x] Create RBAC schemas (`packages/shared/schemas/rbac.py`)
- [x] Create tenant schemas (`packages/shared/schemas/tenant.py`)
- [x] Create RBAC client (`packages/shared/clients/rbac.py`)
- [ ] Update document schema with `client_id` and `project_id`
- [ ] Create migration script for existing documents

### **Phase 2: Backend API (Week 2)**
- [ ] Create client management endpoints
  - POST `/api/admin/clients` - Create client
  - GET `/api/admin/clients` - List clients
  - GET `/api/admin/clients/{id}` - Get client details
  - PUT `/api/admin/clients/{id}` - Update client
  
- [ ] Create project management endpoints
  - POST `/api/admin/projects` - Create project
  - GET `/api/admin/projects` - List projects (filtered by client)
  - GET `/api/admin/projects/{id}` - Get project details
  - PUT `/api/admin/projects/{id}` - Update project
  
- [ ] Create user management endpoints
  - POST `/api/admin/users` - Create user
  - GET `/api/admin/users` - List users (filtered by client/project)
  - GET `/api/admin/users/{id}` - Get user details
  - PUT `/api/admin/users/{id}` - Update user
  - POST `/api/admin/users/{id}/assign-client` - Assign to client
  - POST `/api/admin/users/{id}/assign-project` - Assign to project

### **Phase 3: Authorization Middleware (Week 2)**
- [ ] Create `require_permission` decorator
- [ ] Create `require_role` decorator
- [ ] Create `require_client_access` decorator
- [ ] Create `require_project_access` decorator
- [ ] Update all existing endpoints with auth checks

### **Phase 4: Frontend UI (Week 3)**
- [ ] Create Client Management page (`/admin/clients`)
- [ ] Create Project Management page (`/admin/projects`)
- [ ] Create User Management page (`/admin/users`)
- [ ] Add client/project selector to header
- [ ] Update document upload to assign to project
- [ ] Filter documents by selected project

### **Phase 5: Migration & Testing (Week 4)**
- [ ] Migrate existing documents to default client/project
- [ ] Create seed data for testing
- [ ] End-to-end testing
- [ ] Security audit
- [ ] Performance testing

---

## 💻 Code Examples

### **Backend: Check Access**

```python
from packages.shared.clients.rbac import RBACClient
from packages.shared.schemas.rbac import PermissionType

rbac = RBACClient()

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str, user_email: str):
    # Check if user has permission to view this document
    user = await rbac.get_user_by_email(user_email)
    can_access = await rbac.check_document_access(
        user.id, 
        doc_id, 
        PermissionType.VIEW_DOCUMENTS
    )
    
    if not can_access:
        raise HTTPException(403, "Access denied")
    
    # Proceed with document retrieval
    ...
```

### **Backend: Filter Documents by Project**

```python
@app.get("/api/inventory")
async def get_inventory(user_email: str, project_id: Optional[str] = None):
    # Get user's tenant context
    context = await rbac.get_tenant_context(user_email)
    
    # If project_id specified, ensure user has access
    if project_id and not context.can_access_project(project_id):
        raise HTTPException(403, "Access denied to this project")
    
    # Filter documents by accessible projects
    accessible_projects = context.project_ids
    if project_id:
        accessible_projects = [project_id]
    
    # Query documents in accessible projects only
    docs = []
    for proj_id in accessible_projects:
        project_docs = await rbac.get_project_documents(proj_id, context.user_id)
        docs.extend(project_docs)
    
    return docs
```

### **Frontend: Client/Project Selector**

```typescript
// In Header component
<select onChange={(e) => setActiveClient(e.target.value)}>
  {userClients.map(client => (
    <option key={client.id} value={client.id}>
      {client.name}
    </option>
  ))}
</select>

<select onChange={(e) => setActiveProject(e.target.value)}>
  {clientProjects.map(project => (
    <option key={project.id} value={project.id}>
      {project.name}
    </option>
  ))}
</select>
```

---

## 📋 Database Migration

### **Migrate Existing Documents:**

```python
# Add to all existing documents
for doc in firestore.collection("documents").stream():
    doc.reference.update({
        "client_id": "default-client",  # Default client for migration
        "project_id": "default-project",  # Default project
        "visibility": "project"
    })
```

### **Create Default Client & Project:**

```python
default_client = Client(
    id="client-transparent-partners",
    name="Transparent Partners",
    domain="transparent.partners",
    status="active",
    created_by="system@transparent.partners",
    contact_email="admin@transparent.partners"
)

default_project = Project(
    id="project-chr-martech",
    client_id="client-transparent-partners",
    name="CHR MarTech Enablement",
    code="CHR-MT",
    status="active",
    created_by="system@transparent.partners"
)
```

---

## 🎨 UI Design

### **New Admin Pages:**

#### **1. Client Management (`/admin/clients`)**
```
┌────────────────────────────────────────────────┐
│  Clients                                  [+ Add Client] │
├────────────────────────────────────────────────┤
│                                                 │
│  Acme Inc                          Active      │
│  acme.com │ 3 projects │ 15 users             │
│  [View] [Edit] [Users] [Projects]             │
│                                                 │
│  XYZ Corp                          Active      │
│  xyzcorp.com │ 1 project │ 8 users            │
│  [View] [Edit] [Users] [Projects]             │
│                                                 │
└────────────────────────────────────────────────┘
```

#### **2. Project Management (`/admin/projects`)**
```
┌────────────────────────────────────────────────┐
│  Projects                            [+ Add Project]     │
│  Client: [All Clients ▼]                        │
├────────────────────────────────────────────────┤
│                                                 │
│  CHR MarTech Enablement               Active   │
│  Client: Acme Inc │ 98 docs │ 5 users         │
│  [View] [Edit] [Documents] [Users]            │
│                                                 │
│  Digital Transformation               Active   │
│  Client: XYZ Corp │ 45 docs │ 3 users         │
│  [View] [Edit] [Documents] [Users]            │
│                                                 │
└────────────────────────────────────────────────┘
```

#### **3. User Management (`/admin/users`)**
```
┌────────────────────────────────────────────────┐
│  Users                                [+ Add User]       │
│  Filter: [All Clients ▼] [All Roles ▼]         │
├────────────────────────────────────────────────┤
│                                                 │
│  john@acme.com                    Account Admin│
│  Acme Inc │ 2 projects assigned                │
│  [View] [Edit] [Assign Projects]              │
│                                                 │
│  jane@acme.com                    Project Admin│
│  Project: CHR MarTech                          │
│  [View] [Edit] [Change Role]                  │
│                                                 │
│  user@acme.com                         End User│
│  Projects: CHR MarTech, Digital Transformation │
│  [View] [Edit] [Revoke Access]                │
│                                                 │
└────────────────────────────────────────────────┘
```

---

## 🔄 User Workflows

### **Workflow 1: Add New Client**
1. Super Admin goes to `/admin/clients`
2. Clicks "+ Add Client"
3. Fills in: Name, Domain, Contact Info
4. System creates client
5. Super Admin assigns Account Admin to client

### **Workflow 2: Add New Project**
1. Super Admin or Account Admin goes to `/admin/projects`
2. Clicks "+ Add Project"
3. Selects Client, enters Project Name, Code
4. Pastes Google Sheets document index URL
5. System creates project and imports documents
6. Admin assigns Project Admin and End Users

### **Workflow 3: Grant User Access**
1. Account Admin goes to `/admin/users`
2. Clicks "+ Add User"
3. Enters email, name, role
4. Assigns to specific projects
5. User receives email invitation
6. User can now access assigned projects

### **Workflow 4: End User Experience**
1. User logs in with email
2. Sees list of accessible projects in dropdown
3. Selects a project (e.g., "CHR MarTech")
4. Views documents and chats with AI
5. Only sees documents from selected project

---

## 🎯 Implementation Priority

### **MVP (Minimum Viable Product) - 2 Weeks**
✅ Core schemas created  
⏳ Client & Project CRUD APIs  
⏳ User management APIs  
⏳ Basic authorization middleware  
⏳ Frontend client/project selector  
⏳ Document filtering by project  

### **V1.0 (Full Feature) - 4 Weeks**
⏳ All 4 roles fully implemented  
⏳ Complete admin UI  
⏳ Audit logging  
⏳ Access request workflow  
⏳ Migration of existing data  
⏳ Full testing & QA  

### **V2.0 (Advanced) - 6 Weeks**
⏳ Custom permissions per user  
⏳ Document-level access control  
⏳ Usage analytics per client  
⏳ Billing integration  
⏳ API rate limiting per client  
⏳ White-label branding  

---

## 🚀 Next Steps

### **Immediate (This Week):**
1. ✅ Design RBAC architecture (this document)
2. ✅ Create core schemas
3. ⏳ Create client management API
4. ⏳ Create project management API
5. ⏳ Test with sample data

### **Short Term (Next Week):**
1. User management API
2. Authorization middleware
3. Update document APIs
4. Create migration script
5. Build admin UI

### **Before Production:**
1. Security audit
2. Load testing with multiple tenants
3. Data migration plan
4. User documentation
5. Training for admins

---

## 📝 Files Created

1. ✅ `packages/shared/schemas/rbac.py` - Core RBAC models
2. ✅ `packages/shared/schemas/tenant.py` - Multi-tenancy models
3. ✅ `packages/shared/clients/rbac.py` - RBAC client operations
4. ✅ `RBAC_IMPLEMENTATION_PLAN.md` - This document

---

## ❓ Questions to Decide

1. **Default Client:** Should we create "Transparent Partners" as the default client for existing documents?

2. **Migration Strategy:** Should all existing 98 documents go into one project ("CHR MarTech") or should we create multiple projects based on SOW number?

3. **User Onboarding:** How should new users be added? Self-registration + approval? Or invite-only?

4. **Project Codes:** Should we use SOW numbers as project codes? (e.g., "CHR-SOW1", "CHR-SOW2")

5. **Document Visibility:** Should documents be visible at:
   - Project level only (most restrictive)
   - Client level (all projects in client)
   - Public (anyone authenticated)

---

**Ready to implement! What would you like to tackle first?**

1. Create the client & project management APIs
2. Build the admin UI for managing clients/projects/users
3. Migrate your existing 98 documents to the new structure
4. Something else?

