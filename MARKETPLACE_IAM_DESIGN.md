
# Marketplace IAM Integration Design

## 🎯 Vision: Multi-Product Marketplace

```
┌─────────────────────────────────────────────────────────────┐
│                 MARKETPLACE PLATFORM                         │
│  • Central Identity & Access Management                      │
│  • Unified billing & subscriptions                           │
│  • Cross-product SSO                                         │
│  • Organization management                                   │
│  • Usage analytics & monitoring                              │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐  ┌──────────┐
  │ Project  │ │  Agent   │ │  Agent   │  │  Agent   │
  │  Agent   │ │  B       │ │  C       │  │  D       │
  │ (Current)│ │ (Future) │ │ (Future) │  │ (Future) │
  └──────────┘ └──────────┘ └──────────┘  └──────────┘
```

---

## 🏗️ Two-Tier IAM Architecture

### **Tier 1: Marketplace IAM** (Future - Sits Above)
```typescript
{
  user_id: "mk-user-12345",
  org_id: "mk-org-abc",
  subscription_id: "mk-sub-xyz",
  roles: ["org_admin", "billing_admin"],
  permissions: [
    "access_all_products",
    "manage_org_users",
    "view_billing"
  ],
  products: {
    "project-agent": {
      enabled: true,
      tier: "enterprise",
      seats: 50
    },
    "other-agent": {
      enabled: false
    }
  }
}
```

### **Tier 2: Project Agent IAM** (Current - Product-Specific)
```typescript
{
  local_user_id: "user-pa-456",
  external_user_id: "mk-user-12345",  // Reference to marketplace
  identity_provider: "marketplace",
  
  // Project Agent specific permissions
  role: "super_admin",  // Role within THIS product
  client_ids: ["client-acme", "client-xyz"],
  project_ids: ["project-1", "project-2"]
}
```

---

## 🔄 Integration Patterns

### **Pattern 1: Token Delegation** (Recommended)
```
User Login → Marketplace IAM
    ↓
Marketplace IAM issues token
    ↓
User accesses Project Agent
    ↓
Project Agent validates token with Marketplace IAM
    ↓
Project Agent creates local session with local permissions
```

### **Pattern 2: Token Federation**
```
User Login → Marketplace IAM
    ↓
Marketplace IAM issues federated token for Project Agent
    ↓
Project Agent validates locally (JWT with shared secret)
    ↓
Project Agent maps external user to local user
```

### **Pattern 3: API-to-API** (Highest Security)
```
User Login → Marketplace IAM
    ↓
Marketplace sends webhook to Project Agent
    ↓
Project Agent queries Marketplace API for user details
    ↓
Project Agent creates/updates local user mapping
```

---

## 🔌 Implementation in Project Agent

### **Current State (Phase 2):**
```python
# Local auth only
from packages.shared.clients.auth import verify_google_token

user = verify_google_token(token)
# Returns: {email, name, is_admin}
```

### **Future State (Marketplace Ready):**
```python
# Pluggable identity provider
from packages.shared.clients.identity_provider import get_identity_provider

provider = get_identity_provider()  # Could be local OR marketplace
auth_context = await provider.validate_token(token)

# auth_context contains:
# - External identity (if from marketplace)
# - Local Project Agent permissions
# - Unified view of user access
```

---

## 📊 Database Schema Evolution

### **Current (Phase 2):**
```
users/
└── {user_id}
    ├── email: string
    ├── role: string
    ├── client_ids: array
    └── project_ids: array
```

### **Future (Marketplace Integration):**
```
users/
└── {local_user_id}
    ├── email: string
    ├── role: string
    ├── client_ids: array
    ├── project_ids: array
    └── external_identity: {
        ├── provider: "marketplace"
        ├── external_user_id: "mk-user-12345"
        ├── last_synced: timestamp
        └── sync_enabled: boolean
    }

external_user_mappings/
└── {mapping_id}
    ├── local_user_id: "user-pa-456"
    ├── external_user_id: "mk-user-12345"
    ├── provider: "marketplace"
    └── auto_provision: boolean
```

---

## 🔐 Permission Resolution

### **Marketplace + Local Permissions:**

```typescript
function getEffectivePermissions(authContext: AuthContext) {
  const permissions = []
  
  // 1. Marketplace-level permissions (if federated)
  if (authContext.marketplace_context) {
    if (authContext.marketplace_context.marketplace_roles.includes('platform_admin')) {
      return ['*']  // Full access to everything
    }
    
    if (!authContext.marketplace_context.product_access['project-agent']?.enabled) {
      return []  // No access to this product
    }
  }
  
  // 2. Project Agent local permissions
  const localRole = authContext.local_role
  permissions.push(...getLocalRolePermissions(localRole))
  
  // 3. Subscription-based limits
  if (authContext.marketplace_context?.subscription_tier === 'free') {
    permissions = permissions.filter(p => !PREMIUM_PERMISSIONS.includes(p))
  }
  
  return permissions
}
```

---

## 🚀 Migration Path

### **Phase 2 (Current): Local IAM Only**
```
✅ Project Agent has own user management
✅ Local authentication (Google OAuth)
✅ Product-specific RBAC
✅ No external dependencies
```

### **Phase 3 (Future): Marketplace Integration Prep**
```
⏳ Add identity_provider abstraction layer
⏳ Support external_user_id references
⏳ Implement user mapping table
⏳ Add marketplace_context to AuthContext
```

### **Phase 4 (Future): Full Marketplace Integration**
```
⏳ Connect to marketplace IAM API
⏳ Validate tokens against marketplace
⏳ Sync user profiles automatically
⏳ Inherit marketplace roles/permissions
⏳ Support subscription-based limits
```

---

## 💡 Design Principles

### **1. Abstraction**
✅ Never directly reference "local" auth in business logic  
✅ Always use `get_identity_provider()` interface  
✅ Business logic doesn't know WHERE user came from  

### **2. Loose Coupling**
✅ Project Agent can run standalone (local IAM)  
✅ OR integrated with marketplace (federated IAM)  
✅ Switch providers with configuration change only  

### **3. Data Ownership**
✅ Marketplace IAM owns: user identity, org membership, billing  
✅ Project Agent owns: product permissions, client/project access  
✅ Clear separation of concerns  

### **4. Fallback Strategy**
✅ If marketplace unavailable → use cached local permissions  
✅ Graceful degradation  
✅ Never block access due to external service outage  

---

## 🎯 Immediate Benefits

Even without marketplace integration, this design gives you:

1. ✅ **Future-proof** - Easy to plug in marketplace later
2. ✅ **Flexible** - Can add Google SSO, Azure AD, Okta, etc.
3. ✅ **Testable** - Mock providers for testing
4. ✅ **Clean** - Business logic doesn't change when adding providers

---

## 📝 Code Example

### **Current Code (Phase 2):**
```python
# In any endpoint
@app.get("/documents")
async def get_documents(user: dict = Depends(require_domain_auth)):
    user_email = user["email"]
    # Use email directly
```

### **Future-Ready Code:**
```python
# Same endpoint, marketplace-ready
from packages.shared.clients.identity_provider import get_identity_provider

@app.get("/documents")
async def get_documents(token: str = Depends(get_bearer_token)):
    provider = get_identity_provider()
    auth_context = await provider.validate_token(token)
    
    # Works with local OR marketplace IAM!
    user_email = auth_context.email
    user_role = auth_context.get_effective_role()
    
    # Check if from marketplace
    if auth_context.is_from_marketplace():
        logger.info(f"Marketplace user {auth_context.marketplace_context.marketplace_user_id} accessing")
```

---

## 🎉 Summary

**What We Built:**
- ✅ Identity provider abstraction layer
- ✅ Support for external identity references
- ✅ User mapping between systems
- ✅ Marketplace context schema
- ✅ Pluggable auth architecture

**What This Enables:**
- 🔮 Future marketplace IAM integration (zero refactoring)
- 🔮 Support for any SSO provider
- 🔮 Federation with external systems
- 🔮 Subscription-based access control

**Status:**  
✅ **Project Agent works standalone today**  
✅ **Ready to plug into marketplace tomorrow**  
✅ **No technical debt, future-proof design**

---

**Your RBAC system is now enterprise-grade AND marketplace-ready!** 🚀

