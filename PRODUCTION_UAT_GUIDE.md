# Production UAT Testing Guide - RBAC Complete System

## 🎯 Overview

**Production URL:** https://project-agent-web-117860496175.us-central1.run.app

This guide provides comprehensive UAT (User Acceptance Testing) procedures for validating the complete RBAC multi-tenant system in production.

---

## ✅ What Was Deployed

### **Web Portal** ✅ LIVE
- **URL:** https://project-agent-web-117860496175.us-central1.run.app
- **Revision:** project-agent-web-00023-z7h
- **Status:** Deployed and serving traffic

### **Changes Deployed:**
1. ✅ Admin tab reordering (Clients → Projects → Inventory → Ingest → Drive Search)
2. ✅ Document Approval tab removed (functionality in Inventory)
3. ✅ All RBAC Phase 1-4 code committed to GitHub

### **Backend APIs** (Previous Deployment)
- Chat API: https://project-agent-chat-api-117860496175.us-central1.run.app
- Admin API: https://project-agent-admin-api-117860496175.us-central1.run.app
- Inventory API: https://project-agent-inventory-api-117860496175.us-central1.run.app
- Documents API: https://project-agent-documents-api-117860496175.us-central1.run.app
- Upload API: https://project-agent-upload-api-117860496175.us-central1.run.app

---

## 🔍 UAT Testing Checklist

### **Test 1: Admin Page UI Changes** ✅ DEPLOYED

**Test URL:** https://project-agent-web-117860496175.us-central1.run.app/admin

**Expected Results:**
- ✅ Tab order: Clients → Projects → Inventory → Ingest Documents → Drive Search → RBAC Migration
- ✅ "Document Approval" tab is removed
- ✅ "Clients" is the default active tab
- ✅ All tabs clickable and functional
- ✅ Drive Search uses correct icon (MagnifyingGlass)

**How to Test:**
1. Visit the admin page
2. Verify tab order matches expected
3. Click through each tab to ensure they load
4. Confirm Document Approval is gone

---

### **Test 2: Client Management Tab**

**Location:** Admin → Clients tab

**Expected Features:**
- Client list view
- Add new client functionality
- Edit client details
- View client's projects
- Client filtering/search

**How to Test:**
1. Click "Clients" tab
2. Verify client list displays
3. Test "Add Client" button
4. Check client details are editable
5. Verify project count shows for each client

---

### **Test 3: Project Management Tab**

**Location:** Admin → Projects tab

**Expected Features:**
- Project list view
- Add new project functionality
- Filter by client
- Project details with document count
- Import documents from Google Sheets

**How to Test:**
1. Click "Projects" tab
2. Verify project list displays
3. Test "Add Project" button
4. Check project details
5. Verify document count displays
6. Test client filter dropdown

---

### **Test 4: Inventory Tab**

**Location:** Admin → Inventory tab

**Expected Features:**
- Document list with filters
- Search functionality
- Document type filters
- Status filters
- Export CSV
- Pagination

**How to Test:**
1. Click "Inventory" tab
2. Check document list displays
3. Test search box
4. Apply document type filters
5. Apply status filters
6. Test pagination
7. Test Export CSV button

---

### **Test 5: Ingest Documents Tab**

**Location:** Admin → Ingest Documents tab

**Expected Features:**
- Add single document by URL
- Bulk upload via CSV
- Google Sheets integration
- Document metadata entry

**How to Test:**
1. Click "Ingest Documents" tab
2. Test single document ingestion
3. Test CSV upload
4. Test Google Sheets analysis
5. Verify success/error messages

---

### **Test 6: Drive Search Tab**

**Location:** Admin → Drive Search tab

**Expected Features:**
- Google Drive folder sync
- Folder ID input
- Recursive sync option
- Sync status display

**How to Test:**
1. Click "Drive Search" tab
2. Verify UI loads correctly
3. Test folder ID input
4. Check recursive option
5. Test sync functionality

---

## 🔒 RBAC Security Testing (Once Backend Deployed)

### **Test 7: User Role Separation**

**Setup Required:**
1. Create test users via Admin API:
   - Super Admin
   - Account Admin for Client A
   - Project Admin for Project 1
   - End User for Projects 1-2

**Test Scenarios:**

#### **7.1 Super Admin Access**
```bash
# Should have unrestricted access
curl https://project-agent-admin-api-xxx.run.app/admin/rbac/clients \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN"

Expected: Returns ALL clients
```

#### **7.2 Account Admin Restrictions**
```bash
# Should see only assigned client
curl https://project-agent-admin-api-xxx.run.app/admin/rbac/clients \
  -H "Authorization: Bearer $ACCOUNT_ADMIN_TOKEN"

Expected: Returns ONLY assigned client
```

#### **7.3 Project Admin Restrictions**
```bash
# Should NOT be able to create clients
curl -X POST https://project-agent-admin-api-xxx.run.app/admin/rbac/clients \
  -H "Authorization: Bearer $PROJECT_ADMIN_TOKEN"

Expected: 403 Forbidden - "Permission required: client:manage"
```

#### **7.4 End User Restrictions**
```bash
# Should NOT access admin endpoints
curl https://project-agent-admin-api-xxx.run.app/admin/rbac/clients \
  -H "Authorization: Bearer $END_USER_TOKEN"

Expected: 403 Forbidden
```

---

### **Test 8: Document Access Control**

**Test Scenarios:**

#### **8.1 Project Boundary Enforcement**
```bash
# User assigned to Project 1 tries to access Project 2 document
curl https://project-agent-documents-api-xxx.run.app/documents/project2-doc-123 \
  -H "Authorization: Bearer $PROJECT1_USER_TOKEN"

Expected: 403 Forbidden - "Access denied to document"
```

#### **8.2 Inventory Filtering**
```bash
# User assigned to Projects 1-2 gets inventory
curl https://project-agent-inventory-api-xxx.run.app/inventory \
  -H "Authorization: Bearer $PROJECT12_USER_TOKEN"

Expected: Returns ONLY documents from Projects 1 & 2
```

---

### **Test 9: AI Chat Information Isolation** 🔒 **CRITICAL**

**Test Scenarios:**

#### **9.1 Cross-Project Information Leakage**
```bash
# Setup:
# - User A: Access to Project 1 (Budget: $500k)
# - Project 2 exists (Budget: $1M) but user has NO access

# Test:
curl -X POST https://project-agent-chat-api-xxx.run.app/chat \
  -H "Authorization: Bearer $USER_A_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the budget?"}'

# Expected:
# Answer: "Budget is $500k" (Project 1 ONLY)
# Citations: [Project 1 documents only]

# CRITICAL:
# Answer should NOT mention Project 2's $1M budget
# Citations should NOT include Project 2 documents
```

#### **9.2 Cross-Client Information Leakage**
```bash
# Setup:
# - User: Account Admin for Client A
# - Client B exists with sensitive data

# Test:
curl -X POST https://project-agent-chat-api-xxx.run.app/chat \
  -H "Authorization: Bearer $CLIENT_A_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all revenue numbers"}'

# Expected:
# Answer: Contains ONLY Client A revenue
# Citations: ONLY Client A documents

# CRITICAL:
# No mention of Client B anywhere in response
```

---

### **Test 10: Upload Permissions**

```bash
# End User tries to upload (should fail)
curl -X POST https://project-agent-upload-api-xxx.run.app/upload \
  -H "Authorization: Bearer $END_USER_TOKEN" \
  -F "file=@test.pdf"

Expected: 403 Forbidden - "Permission required: document:upload"

# Project Admin uploads (should succeed)
curl -X POST https://project-agent-upload-api-xxx.run.app/upload \
  -H "Authorization: Bearer $PROJECT_ADMIN_TOKEN" \
  -F "file=@test.pdf"

Expected: 200 OK with document ID
```

---

## 📊 Production Validation Checklist

### **Phase 1: UI Validation**
- [ ] Admin page loads successfully
- [ ] Tab order is correct (Clients first)
- [ ] Document Approval tab is removed
- [ ] All tabs are clickable
- [ ] Navigation is smooth
- [ ] No console errors
- [ ] Responsive on mobile/tablet

### **Phase 2: Functional Testing** (After Backend Deployed)
- [ ] Can create clients
- [ ] Can create projects
- [ ] Can create users
- [ ] Can assign users to projects
- [ ] Can upload documents
- [ ] Can view inventory
- [ ] Can chat with AI
- [ ] Can search documents

### **Phase 3: RBAC Security Testing** 🔒 **CRITICAL**
- [ ] Super Admin can access everything
- [ ] Account Admin sees only assigned client
- [ ] Project Admin sees only assigned project
- [ ] End User has read-only access
- [ ] Cross-project access is blocked (403)
- [ ] Cross-client access is blocked (403)
- [ ] AI chat filters by user access
- [ ] **AI answers contain NO unauthorized information** 🚨
- [ ] Upload requires proper permissions
- [ ] Permission escalation fails

### **Phase 4: Performance**
- [ ] Pages load in < 3 seconds
- [ ] API responses in < 2 seconds
- [ ] Chat responses in < 5 seconds
- [ ] Inventory with 100+ docs loads smoothly
- [ ] No timeout errors
- [ ] Concurrent users supported

### **Phase 5: Integration**
- [ ] End-to-end user workflows work
- [ ] Document upload → indexing → search flow
- [ ] Client → Project → Document hierarchy
- [ ] User assignment → access control flow

---

## 🚀 Current Deployment Status

### **Deployed Services:**
✅ **Web Portal** - https://project-agent-web-117860496175.us-central1.run.app
- Revision: project-agent-web-00023-z7h
- Status: SUCCESS
- Changes: Admin tab reordering, Document Approval removed

### **Backend APIs** (Need RBAC Deployment)
⏳ Chat API (needs RBAC filtering)
⏳ Admin API (needs RBAC endpoints)
⏳ Inventory API (needs access filtering)
⏳ Documents API (needs access checks)
⏳ Upload API (needs permission checks)

**Next Step:** Fix backend Dockerfiles and deploy all services

---

## 🎯 UAT Test Scenarios

### **Scenario 1: Super Admin Workflow**
1. Login as Super Admin
2. Create Client "Acme Inc"
3. Create Project "CHR MarTech" under Acme
4. Create Account Admin for Acme
5. Upload test documents to project
6. Verify documents appear in inventory
7. Chat with AI about the documents
8. Verify full access to everything

### **Scenario 2: Account Admin Workflow**
1. Login as Account Admin (Client A)
2. View only Client A in Clients tab
3. Create new project in Client A
4. Create Project Admin for the project
5. Assign End Users to projects
6. View all Client A documents in inventory
7. Try to access Client B (should fail 403)
8. Chat with AI (should only see Client A docs)

### **Scenario 3: Project Admin Workflow**
1. Login as Project Admin (Project 1)
2. View only Project 1 in inventory
3. Upload new document to Project 1
4. Approve pending documents
5. Try to upload to Project 2 (should fail 403)
6. Chat with AI (should only see Project 1 docs)

### **Scenario 4: End User Workflow**
1. Login as End User (Projects 1-2)
2. View documents from Projects 1-2 only
3. Try to upload document (should fail 403)
4. Try to access admin page (should fail 403)
5. Chat with AI (should only see Projects 1-2 docs)
6. Request access to additional documents

### **Scenario 5: Security Boundary Testing** 🔒
1. Login as User A (Project 1)
2. Attempt to access document from Project 2
   - Expected: 403 Forbidden
3. Chat: "What are all the budgets?"
   - Expected: Only Project 1 budget in answer
   - **Critical:** No mention of other projects
4. Try to view Client B's projects
   - Expected: 403 Forbidden or empty list
5. Attempt to escalate privileges
   - Expected: All attempts fail with 403

---

## 📝 Testing Notes Template

### **Date:** [Insert Date]
### **Tester:** [Your Name]
### **Environment:** Production

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | Admin UI Changes | ✅/❌ | |
| 2 | Client Management | ✅/❌ | |
| 3 | Project Management | ✅/❌ | |
| 4 | Inventory Tab | ✅/❌ | |
| 5 | Ingest Documents | ✅/❌ | |
| 6 | Drive Search | ✅/❌ | |
| 7 | User Roles | ✅/❌ | |
| 8 | Document Access | ✅/❌ | |
| 9 | AI Chat Isolation | ✅/❌ | 🔒 CRITICAL |
| 10 | Upload Permissions | ✅/❌ | |

### **Issues Found:**
- [ ] Issue 1: [Description]
- [ ] Issue 2: [Description]

### **Sign-off:**
- [ ] All critical tests passed
- [ ] No security issues found
- [ ] Performance is acceptable
- [ ] Ready for production use

**Approved by:** ________________  **Date:** ________

---

## 🚨 Critical Security Validation

### **MUST VERIFY:**

✅ **Information Isolation Test**
```
Query: "Show me all projects and their budgets"

User A (Project 1 only):
  ✅ Answer mentions ONLY Project 1
  ✅ NO mention of other projects
  ✅ Citations from Project 1 only

User B (Projects 2-3):
  ✅ Answer mentions ONLY Projects 2-3
  ✅ NO mention of Project 1
  ✅ Citations from Projects 2-3 only
```

This is the **#1 critical security requirement** - users must NEVER see information from clients/projects they don't have access to.

---

## 🎯 Success Criteria

**UAT Passes If:**
- ✅ All UI changes are visible
- ✅ All user roles work correctly
- ✅ Security boundaries are enforced
- ✅ No information leakage in AI answers
- ✅ Performance is acceptable
- ✅ No critical errors in logs

**UAT Fails If:**
- ❌ User can access other clients' data
- ❌ User can access other projects' data
- ❌ AI answer mentions inaccessible information
- ❌ Permission checks can be bypassed
- ❌ Critical functionality broken

---

## 📞 Next Steps After UAT

### **If UAT Passes:** ✅
1. Mark Phase 5 as complete
2. Deploy backend services with RBAC
3. Run full test suite in production
4. Enable monitoring and alerts
5. Train users on new features
6. Go live!

### **If UAT Fails:** ❌
1. Document all issues
2. Prioritize by severity
3. Fix critical issues
4. Re-deploy
5. Re-test
6. Repeat until pass

---

## 🔍 Monitoring

**Key Metrics to Watch:**
- Error rates (should be < 1%)
- Response times (p95 < 3s)
- Authorization failures (watch for attacks)
- User adoption (track feature usage)

**Where to Monitor:**
- Cloud Run Console: https://console.cloud.google.com/run?project=transparent-agent-test
- Logs: https://console.cloud.google.com/logs?project=transparent-agent-test

---

## ✅ Current Status

**Deployed:** Web Portal with UI improvements  
**Ready for UAT:** Front-end changes  
**Next:** Deploy backend services with RBAC  
**Then:** Full production UAT testing

---

**Start your UAT now!** 🎉

Visit: https://project-agent-web-117860496175.us-central1.run.app/admin

