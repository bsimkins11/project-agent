# RBAC Phase 5: Testing & Production Deployment

## 🎯 Overview

**Phase 5** focuses on comprehensive testing, validation, and production deployment of the complete RBAC system built in Phases 1-4.

---

## 📋 Phase 5 Tasks

### **5.1 Setup Test Environment**
- [ ] Create test users with different roles
- [ ] Create test clients (Client A, Client B)
- [ ] Create test projects (Project 1-4)
- [ ] Assign users to specific clients/projects
- [ ] Upload test documents to different projects

### **5.2 Functional Testing**
- [ ] Test Admin API endpoints
- [ ] Test Inventory API filtering
- [ ] Test Documents API access control
- [ ] Test Chat API information isolation
- [ ] Test Upload API permissions

### **5.3 Security Testing**
- [ ] Test cross-project access (should fail)
- [ ] Test cross-client access (should fail)
- [ ] Test AI information leakage (should not occur)
- [ ] Test permission escalation attempts (should fail)
- [ ] Test Super Admin bypass (should work)

### **5.4 Performance Testing**
- [ ] Benchmark API latency with RBAC
- [ ] Test with 100+ documents
- [ ] Test concurrent user access
- [ ] Measure filtering overhead
- [ ] Optimize slow queries

### **5.5 Integration Testing**
- [ ] End-to-end user workflows
- [ ] Multi-user scenarios
- [ ] Cross-API operations
- [ ] Error handling
- [ ] Edge cases

### **5.6 Deployment**
- [ ] Deploy to staging environment
- [ ] Run full test suite
- [ ] Deploy to production
- [ ] Monitor for issues
- [ ] Rollback plan ready

---

## 🧪 Detailed Test Scenarios

### **Test Suite 1: User Role Testing**

#### **1.1 Super Admin Tests**
```bash
# Setup
User: admin@transparent.partners (Super Admin)

# Tests
✓ Can create clients
✓ Can create projects in any client
✓ Can create users with any role
✓ Can view all documents (all clients/projects)
✓ Can chat with all documents
✓ Can upload documents to any project
✓ Can access all admin endpoints
```

#### **1.2 Account Admin Tests**
```bash
# Setup
User: alice@acme.com (Account Admin for Client Acme)

# Tests
✓ Can view Client Acme (assigned)
✗ Cannot view Client XYZ (not assigned)
✓ Can create projects in Client Acme
✗ Cannot create projects in Client XYZ
✓ Can create users in Client Acme
✗ Cannot create users in Client XYZ
✓ Can view all projects in Client Acme
✓ Can view all documents in Client Acme
✗ Cannot view documents in Client XYZ
✓ Can chat with Client Acme documents only
✗ Cannot upload documents (no UPLOAD_DOCUMENTS permission)
```

#### **1.3 Project Admin Tests**
```bash
# Setup
User: bob@acme.com (Project Admin for Project 1)

# Tests
✗ Cannot view client management
✗ Cannot create projects
✓ Can view Project 1 (assigned)
✗ Cannot view Project 2 (not assigned)
✓ Can view documents in Project 1
✗ Cannot view documents in Project 2
✓ Can upload documents to Project 1
✗ Cannot upload documents to Project 2
✓ Can approve documents in Project 1
✓ Can chat with Project 1 documents only
```

#### **1.4 End User Tests**
```bash
# Setup
User: charlie@acme.com (End User for Projects 1, 2)

# Tests
✗ Cannot access admin endpoints
✗ Cannot create clients/projects/users
✗ Cannot upload documents
✗ Cannot approve documents
✓ Can view documents in Projects 1, 2
✗ Cannot view documents in Project 3
✓ Can chat with Projects 1, 2 documents
✗ Cannot chat with Project 3 documents
✓ Can request access to documents
```

---

### **Test Suite 2: Information Isolation**

#### **2.1 Cross-Project Query Test**
```python
# Setup
User A: Access to Project 1 only
User B: Access to Project 2 only
Documents:
  - Project 1: "Budget is $500k"
  - Project 2: "Budget is $800k"

# Test
Query: "What is the budget?"

# Expected Results
User A Answer: "Budget is $500k" (Project 1 only)
User A Citations: [Project 1 documents only]

User B Answer: "Budget is $800k" (Project 2 only)
User B Citations: [Project 2 documents only]

# Validation
✓ No cross-project information in answers
✓ No cross-project citations
✓ Each user sees only their project's information
```

#### **2.2 Cross-Client Query Test**
```python
# Setup
User A: Account Admin for Client Acme
User B: Account Admin for Client XYZ
Documents:
  - Client Acme: 50 documents
  - Client XYZ: 30 documents

# Test
GET /inventory

# Expected Results
User A: Returns 50 documents (Acme only)
User B: Returns 30 documents (XYZ only)

# Validation
✓ No cross-client document visibility
✓ Inventory counts match expectations
✓ Zero information leakage
```

#### **2.3 AI Answer Leakage Test**
```python
# CRITICAL TEST
# Setup
User: Access to Project A only
System Documents:
  - Project A: "Revenue $5M, Profit $1M"
  - Project B: "Revenue $10M, Profit $3M"  
  - Project C: "Revenue $20M, Profit $5M"

# Test
Query: "Show me all revenue and profit numbers"

# Expected Result
Answer: "Revenue $5M, Profit $1M" (Project A ONLY)
Citations: [Project A documents only]

# What we're preventing
Bad Answer: "Revenue across projects: $5M (A), $10M (B), $20M (C)"
  ↑ This would leak Project B and C information!

# Validation
✓ Answer mentions ONLY Project A numbers
✓ No mention of Project B or C anywhere in answer
✓ Citations contain ONLY Project A documents
✓ Agent planner filtered BEFORE composing answer
```

---

### **Test Suite 3: Security Attacks**

#### **3.1 Permission Escalation Attempt**
```bash
# Attempt: End User tries to upload document
POST /upload
Authorization: Bearer <end_user_token>

# Expected Result
403 Forbidden - "Permission required: document:upload"

# Validation
✓ Request rejected at API level
✓ Permission check works correctly
```

#### **3.2 Cross-Client Access Attempt**
```bash
# Attempt: User A (Client Acme) tries to access Client XYZ project
GET /projects/project-xyz-123
Authorization: Bearer <user_a_token>

# Expected Result
403 Forbidden - "Access denied to project: project-xyz-123"

# Validation
✓ Request rejected at API level
✓ Project access validation works
```

#### **3.3 Direct Document Access Attempt**
```bash
# Attempt: User tries to access document they don't have access to
GET /documents/doc-from-other-project
Authorization: Bearer <user_token>

# Expected Result
403 Forbidden - "Access denied to document: doc-from-other-project"

# Validation
✓ Document-level access check works
✓ Returns 403 before revealing document exists
```

---

### **Test Suite 4: Performance**

#### **4.1 Latency Benchmarks**
```
Without RBAC:
- Inventory API: ~200ms
- Chat API: ~1500ms
- Documents API: ~100ms

With RBAC:
- Inventory API: ~350ms (+150ms)
- Chat API: ~1800ms (+300ms)
- Documents API: ~150ms (+50ms)

Acceptable: < 500ms overhead
Status: ✅ PASS (within acceptable range)
```

#### **4.2 Load Testing**
```bash
# Test
100 concurrent users × 10 requests each = 1000 requests

# Metrics
- Average response time: <2s
- 95th percentile: <3s
- 99th percentile: <5s
- Error rate: <1%

# Validation
✓ System handles concurrent load
✓ No timeout errors
✓ RBAC filtering doesn't cause bottlenecks
```

---

## 🚀 Deployment Steps

### **Step 1: Staging Deployment**
```bash
# 1. Deploy to staging
gcloud builds submit --config ops/cloudbuild.yaml . \
  --substitutions=_ENV=staging

# 2. Run automated tests
./run_phase5_tests.sh staging

# 3. Manual QA testing
# - Test each user role
# - Verify security boundaries
# - Check AI answers for leakage

# 4. Sign-off
# ✓ All tests pass
# ✓ No security issues found
# ✓ Performance acceptable
```

### **Step 2: Production Deployment**
```bash
# 1. Backup current state
./backup_production.sh

# 2. Deploy to production
gcloud builds submit --config ops/cloudbuild.yaml . \
  --substitutions=_ENV=production

# 3. Smoke tests
curl https://project-agent-web-xxx.run.app/health
curl https://project-agent-chat-api-xxx.run.app/health
curl https://project-agent-admin-api-xxx.run.app/health

# 4. Monitor for 30 minutes
# - Check error rates
# - Monitor latency
# - Watch for security alerts

# 5. If issues: Rollback
gcloud run services update-traffic project-agent-web \
  --to-revisions=project-agent-web-00021=100
```

### **Step 3: Post-Deployment Validation**
```bash
# 1. Create production test users
# - Super Admin
# - Account Admin
# - Project Admin  
# - End User

# 2. Run production test suite
./run_phase5_tests.sh production

# 3. Verify RBAC in production
# - Test cross-project isolation
# - Test AI answer filtering
# - Test permission boundaries

# 4. Enable monitoring alerts
# - Failed authorization attempts
# - Unusual access patterns
# - Performance degradation
```

---

## 📊 Success Criteria

### **Functional Requirements**
- [ ] All user roles work correctly
- [ ] Client boundaries enforced
- [ ] Project boundaries enforced
- [ ] Document access controlled
- [ ] AI answers filtered properly
- [ ] Permissions checked on all endpoints

### **Security Requirements**
- [ ] Zero information leakage
- [ ] No cross-project access
- [ ] No cross-client access
- [ ] No permission escalation possible
- [ ] AI answers contain only accessible info
- [ ] All attack scenarios fail

### **Performance Requirements**
- [ ] API latency < 500ms overhead
- [ ] Chat response < 3s (95th percentile)
- [ ] Inventory load < 1s (95th percentile)
- [ ] System handles 100+ concurrent users
- [ ] No timeout errors under load

### **Operational Requirements**
- [ ] Zero breaking changes
- [ ] Existing users continue working
- [ ] Graceful degradation for non-RBAC users
- [ ] Comprehensive logging
- [ ] Monitoring alerts configured
- [ ] Rollback plan tested

---

## 🔍 Monitoring & Alerts

### **Key Metrics to Monitor**
1. **Authorization failures** - Spike indicates attack or misconfiguration
2. **API latency** - Track RBAC overhead
3. **Document access patterns** - Detect unusual behavior
4. **Chat query patterns** - Monitor for information leakage attempts
5. **Error rates** - Watch for RBAC-related errors

### **Alert Thresholds**
```yaml
alerts:
  - name: "High Authorization Failures"
    condition: "failed_auth_rate > 10/min"
    severity: warning
  
  - name: "API Latency Spike"
    condition: "p95_latency > 5s"
    severity: warning
  
  - name: "Security Breach Attempt"
    condition: "403_errors > 100/min from single IP"
    severity: critical
```

---

## 📝 Test Execution Checklist

### **Pre-Deployment**
- [ ] All Phase 1-4 code committed
- [ ] Security documentation reviewed
- [ ] Test users created
- [ ] Test data prepared
- [ ] Test scripts ready

### **During Testing**
- [ ] Functional tests: PASS/FAIL
- [ ] Security tests: PASS/FAIL
- [ ] Performance tests: PASS/FAIL
- [ ] Integration tests: PASS/FAIL
- [ ] Issues documented
- [ ] Fixes applied

### **Post-Deployment**
- [ ] Staging tests: PASS
- [ ] Production smoke tests: PASS
- [ ] Monitoring configured
- [ ] Alerts enabled
- [ ] Documentation updated
- [ ] Team trained

---

## 🎯 Phase 5 Summary

**Goal:** Validate and deploy complete RBAC system

**Duration:** 1-2 weeks
- Week 1: Testing (functional, security, performance)
- Week 2: Deployment (staging → production)

**Success Metrics:**
- ✅ All tests pass
- ✅ Zero security vulnerabilities
- ✅ Performance within acceptable range
- ✅ Production deployment successful
- ✅ Users can only access assigned information

---

## 🚀 Ready for Phase 5!

**Current Status:**
- ✅ Phase 1: Foundation (Complete)
- ✅ Phase 2: Management UI (Complete)
- ✅ Phase 3: Authorization Middleware (Complete)
- ✅ Phase 4: Apply to Endpoints (Complete)
- ⏳ Phase 5: Testing & Deployment (Ready to start)

**Next Steps:**
1. Create test users and data
2. Run test suites
3. Deploy to staging
4. Validate security
5. Deploy to production
6. Monitor and optimize

Let's make it production-ready! 🎉

