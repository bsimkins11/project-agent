# Parent-Child IAM Design: Marketplace ↔ Project Agent

## 🎯 Design Principle

**Marketplace/Portal IAM is the PARENT (source of truth)**  
**Project Agent IAM is the CHILD (receives and extends)**

---

## 📊 Responsibility Split

### **Marketplace/Portal IAM (Parent) - Controls:**
1. ✅ User authentication
2. ✅ Product access (which agents)
3. ✅ **Base role assignment** ← Marketplace decides!
4. ✅ Organization membership
5. ✅ Subscription/billing

### **Project Agent IAM (Child) - Controls:**
1. ✅ Receives role from parent
2. ✅ Adds client/project assignments (product-specific)
3. ✅ Adds document-level permissions (product-specific)
4. ✅ Maps parent role to product capabilities
5. ✅ Extends with product workflows

---

## 🔄 Information Flow

```
Marketplace IAM (Parent)
    │
    │ Sends:
    ├─ user_id: "mk-12345"
    ├─ email: "john@company.com"
    ├─ role: "org_admin"  ← SOURCE OF TRUTH
    ├─ org_id: "org-acme"
    └─ product_access: ["project-agent"]
    │
    ▼
Project Agent (Child)
    │
    │ Receives parent data
    ├─ Accepts role: "org_admin"
    ├─ Maps to: account_admin (in Project Agent)
    │
    │ Adds product-specific:
    ├─ client_ids: ["client-acme"]
    ├─ project_ids: ["proj-1", "proj-2"]
    └─ document permissions based on projects
```

---

## 💡 Role Mapping Strategy

### **Marketplace Roles → Project Agent Roles**

| Marketplace Role (Parent) | Project Agent Role (Child) | Auto-Grants |
|---------------------------|---------------------------|-------------|
| `platform_admin` | `super_admin` | All clients, all projects |
| `org_admin` | `account_admin` | All client's projects |
| `org_user` | `end_user` | Explicitly assigned projects only |
| `org_viewer` | `end_user` (read-only) | Explicitly assigned projects only |

**Key Point:** Marketplace role is **accepted as-is**, then mapped to product equivalent.

---

## 🏗️ Current Design (Marketplace-Ready)

### **What We Built:**

```python
class ProjectAgentUserContext:
    product_role: ProductRole           # Our role (can be overridden by marketplace)
    role_source: str                    # "marketplace" | "local"
    marketplace_context: Optional[...]  # Parent context (if federated)
```

**When marketplace is ready:**
```python
# Marketplace sends role
marketplace_user = {
    "user_id": "mk-12345",
    "role": "org_admin"  # Marketplace decides this
}

# Project Agent accepts and maps
product_role = map_marketplace_role(marketplace_user.role)
# product_role = "account_admin" (mapped from "org_admin")

# Project Agent cannot override - must respect parent's role assignment
```

---

## 🔒 Role Authority

### **Parent (Marketplace) Has Final Say:**
```
❌ Project Agent CANNOT promote user to higher role than marketplace assigned
✅ Project Agent CAN restrict to lower access (e.g., limit to specific projects)
❌ Project Agent CANNOT change user's base role
✅ Project Agent CAN add product-specific permissions within role bounds
```

### **Example:**
```
Marketplace says: "User is org_user" (regular user)
    ↓
Project Agent maps to: "end_user"
    ↓
Project Agent CANNOT make them "super_admin"
    ↓
Project Agent CAN assign to specific projects
    ↓
Result: End user with access to Project 1 & 2 only
```

---

## 🔌 Integration Contract

### **What Marketplace Sends to Project Agent:**

```typescript
interface MarketplaceAuthToken {
  // Identity
  user_id: string                    // Marketplace user ID
  email: string
  name: string
  
  // Organization
  org_id: string
  org_name: string
  
  // Role (SOURCE OF TRUTH)
  role: "platform_admin" | "org_admin" | "org_user" | "org_viewer"
  
  // Product access
  products: {
    "project-agent": {
      enabled: true,
      tier: "enterprise",
      // Optional: Marketplace can also send product-specific assignments
      assignments?: {
        clients?: string[],
        projects?: string[]
      }
    }
  }
  
  // Token metadata
  iat: number
  exp: number
}
```

### **What Project Agent Does:**

```python
def process_marketplace_user(marketplace_token: MarketplaceAuthToken):
    # 1. Accept role from marketplace (cannot override)
    marketplace_role = marketplace_token.role
    product_role = map_marketplace_to_product_role(marketplace_role)
    
    # 2. Get or create local user mapping
    local_user = get_or_create_local_user(
        external_user_id=marketplace_token.user_id,
        email=marketplace_token.email,
        role=product_role  # Use mapped role from marketplace
    )
    
    # 3. Add product-specific assignments
    # These are Project Agent specific, not from marketplace
    client_ids = get_user_client_assignments(local_user.id)
    project_ids = get_user_project_assignments(local_user.id)
    
    # 4. Return unified context
    return ProjectAgentUserContext(
        local_user_id=local_user.id,
        marketplace_user_id=marketplace_token.user_id,
        product_role=product_role,           # Derived from marketplace
        role_source="marketplace",           # Marketplace is source
        client_ids=client_ids,               # Project Agent specific
        project_ids=project_ids              # Project Agent specific
    )
```

---

## ✅ What This Enables

### **Today (Standalone Mode):**
```python
# Project Agent manages its own roles
user = create_user(email="john@company.com", role="project_admin")
# Role source: local
```

### **Tomorrow (Marketplace Integration):**
```python
# Marketplace sends user with role
marketplace_user = validate_marketplace_token(token)
# {user_id: "mk-123", role: "org_admin"}

# Project Agent accepts the role
user = sync_from_marketplace(marketplace_user)
# Role: account_admin (mapped from org_admin)
# Role source: marketplace
# Cannot be changed locally!
```

---

## 🎯 Key Features

### **1. Parent Authority Respected**
- ✅ Marketplace role is **immutable** in Project Agent
- ✅ Cannot elevate permissions locally
- ✅ Role updates sync from marketplace

### **2. Product-Specific Extensions**
- ✅ Client/project assignments are Project Agent specific
- ✅ Document permissions computed locally
- ✅ Workflow states managed locally

### **3. Graceful Independence**
- ✅ Can run without marketplace (standalone mode)
- ✅ Can switch between local and federated
- ✅ No breaking changes when integrating

---

## 📋 Summary

**Current State:**
- ✅ Project Agent has complete RBAC system
- ✅ Manages own roles locally
- ✅ Client/Project hierarchy working

**Marketplace Integration Ready:**
- ✅ Can receive role from parent IAM
- ✅ Respects parent's role assignment
- ✅ Extends with product-specific permissions
- ✅ Clean parent-child relationship

**What Project Agent Does NOT Do:**
- ❌ Override marketplace role assignments
- ❌ Promote users beyond marketplace role
- ❌ Manage organization membership (marketplace does)
- ❌ Handle billing/subscriptions (marketplace does)

**What Project Agent DOES Do:**
- ✅ Accept role from marketplace
- ✅ Map to product capabilities
- ✅ Manage client/project assignments
- ✅ Handle document-level security
- ✅ Product-specific workflows

---

**Result:** Project Agent is a **well-behaved child** that respects parent IAM decisions while managing its own product-specific access control. 🎯

