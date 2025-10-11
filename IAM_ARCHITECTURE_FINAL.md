# IAM Architecture: Two-Tier Design

## 🎯 Clear Separation of Concerns

### **Tier 1: Marketplace/Portal IAM** (Future - Product Access)
**Responsibility:** Controls **WHICH agents** users can access

```
┌─────────────────────────────────────────────┐
│  MARKETPLACE/PORTAL IAM                      │
│  "Can this user access Project Agent?"      │
├─────────────────────────────────────────────┤
│                                              │
│  User: john@company.com                     │
│  ├─ Project Agent: ✅ GRANTED               │
│  ├─ Analytics Agent: ✅ GRANTED             │
│  ├─ Workflow Agent: ❌ DENIED               │
│  └─ Other Agent: ❌ DENIED                  │
│                                              │
│  Handles:                                    │
│  • Product-level access control             │
│  • Subscription management                  │
│  • Billing & seat licenses                  │
│  • Cross-product navigation                 │
│  • Organization-wide SSO                    │
│                                              │
└─────────────────────────────────────────────┘
```

### **Tier 2: Project Agent IAM** (Current - Within-Product Permissions)
**Responsibility:** Controls **WHAT users can do** within Project Agent

```
┌─────────────────────────────────────────────┐
│  PROJECT AGENT IAM                           │
│  "What can this user do in Project Agent?"  │
├─────────────────────────────────────────────┤
│                                              │
│  User: john@company.com (from marketplace)  │
│  Role in Project Agent: Project Admin       │
│  ├─ Client Access: Client A                 │
│  ├─ Project Access: Project 1, Project 2    │
│  └─ Permissions:                             │
│      ├─ ✅ Upload documents                 │
│      ├─ ✅ Approve documents                │
│      ├─ ✅ Chat with AI                     │
│      ├─ ❌ Manage users                     │
│      └─ ❌ Delete clients                   │
│                                              │
│  Handles:                                    │
│  • Role-based permissions                   │
│  • Client/Project access                    │
│  • Document-level security                  │
│  • Product-specific workflows               │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 🔄 User Journey Example

### **Scenario: User Logs In**

```
Step 1: User visits Marketplace Portal
    ↓
Step 2: Marketplace IAM authenticates user
    ├─ Email: john@company.com
    ├─ Organization: Acme Corp
    └─ Subscription: Enterprise tier
    ↓
Step 3: User sees available agents/products
    ├─ Project Agent ✅ (has access)
    ├─ Analytics Agent ✅ (has access)
    └─ Other Agent ❌ (no subscription)
    ↓
Step 4: User clicks "Project Agent"
    ↓
Step 5: Marketplace redirects to Project Agent with token
    ├─ Token contains: marketplace_user_id, org_id, product_access
    └─ Project Agent validates token with marketplace
    ↓
Step 6: Project Agent checks local permissions
    ├─ Does user exist locally? If not, auto-provision
    ├─ Local role: Project Admin
    ├─ Accessible projects: Project 1, Project 2
    └─ Accessible clients: Client A
    ↓
Step 7: User sees Project Agent interface
    ├─ Header shows: Project selector (only Project 1, 2)
    ├─ Documents filtered to accessible projects
    └─ Admin functions based on local role
```

---

## 🎨 Responsibility Matrix

| Responsibility | Marketplace IAM | Project Agent IAM |
|----------------|-----------------|-------------------|
| **User Authentication** | ✅ Primary | ❌ Delegates to marketplace |
| **Product Access Control** | ✅ Which agents? | ❌ N/A |
| **Organization Management** | ✅ Orgs, billing | ❌ N/A |
| **Subscription Management** | ✅ Tiers, limits | ❌ Receives limits |
| **Cross-Product Navigation** | ✅ Portal nav | ❌ N/A |
| **Role Assignment (in product)** | ❌ N/A | ✅ Local roles |
| **Client/Project Access** | ❌ N/A | ✅ Product-specific |
| **Document Permissions** | ❌ N/A | ✅ Product-specific |
| **Feature Access** | ❌ N/A | ✅ Based on local role |

---

## 💻 Implementation

### **Current State: Standalone Mode**
```python
# Project Agent runs independently
auth_context = await local_provider.validate_token(google_oauth_token)
# Returns: {user_id, email, role, client_ids, project_ids}
```

### **Future State: Marketplace Integration**
```python
# Step 1: Marketplace validates user
marketplace_token = request.headers.get('X-Marketplace-Token')
marketplace_user = await marketplace_iam.validate(marketplace_token)

# Check: Does user have access to Project Agent product?
if not marketplace_user.has_product_access('project-agent'):
    raise HTTPException(403, "No subscription to Project Agent")

# Step 2: Project Agent applies local permissions
local_user = await get_or_create_local_user(marketplace_user.user_id)
auth_context = AuthContext(
    user_id=local_user.id,
    email=marketplace_user.email,
    identity_provider=IdentityProvider.MARKETPLACE,
    is_external=True,
    local_role=local_user.role,  # Project Admin, End User, etc.
    local_client_ids=local_user.client_ids,
    local_project_ids=local_user.project_ids,
    marketplace_context=marketplace_user.to_marketplace_context()
)

# Step 3: Apply permissions
# Marketplace says: "Can access Project Agent" ✅
# Project Agent says: "Can only see Project 1 & 2" ✅
```

---

## 🔑 Key Design Points

### **1. Marketplace IAM = Gatekeeper**
- ✅ "Do you have a subscription?"
- ✅ "Which products can you access?"
- ✅ "What's your organization?"
- ❌ Doesn't know about Project Agent internals

### **2. Project Agent IAM = Product Specialist**
- ✅ "What's your role in THIS product?"
- ✅ "Which clients/projects can you access?"
- ✅ "What documents can you see?"
- ❌ Doesn't handle product access (delegated to marketplace)

### **3. Clean Interface Between Tiers**
```typescript
interface MarketplaceToProjectAgent {
  user_id: string              // Marketplace user ID
  email: string                // User email
  org_id: string               // Organization
  product_access: {
    "project-agent": {
      enabled: true,
      tier: "enterprise",
      seats_used: 15,
      seats_total: 50
    }
  }
}

interface ProjectAgentContext {
  local_user_id: string        // Project Agent user ID
  external_user_id: string     // Reference to marketplace
  role: "super_admin" | "account_admin" | "project_admin" | "end_user"
  client_ids: string[]
  project_ids: string[]
}
```

---

## ✅ What You Get

### **Today (Standalone):**
- ✅ Complete RBAC within Project Agent
- ✅ Client/Project hierarchy
- ✅ Document isolation
- ✅ Runs independently

### **Tomorrow (Marketplace Integration):**
- ✅ Plug into marketplace IAM (no code changes!)
- ✅ Inherit org/subscription context
- ✅ SSO from marketplace portal
- ✅ Keep all Project Agent permissions intact

**The abstraction layer means you can build the marketplace IAM separately and Project Agent will integrate seamlessly!** 🎯

---

## 📋 Files Created

1. `packages/shared/schemas/identity.py` - Identity abstraction
2. `packages/shared/clients/identity_provider.py` - Provider interface
3. `MARKETPLACE_IAM_DESIGN.md` - Architecture doc

**Ready to commit these marketplace-ready improvements?**
