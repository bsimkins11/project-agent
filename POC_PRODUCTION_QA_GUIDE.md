# POC Production QA Guide
## Project Agent - Single Client/Project Architecture

**Date:** October 13, 2025  
**Environment:** Production (Google Cloud Run)  
**Architecture:** Simplified POC - All @transparent.partners users have full access

---

## 🌐 Deployed Services

### Frontend
- **Web Portal:** https://project-agent-web-117860496175.us-central1.run.app
- **Admin Page:** https://project-agent-web-117860496175.us-central1.run.app/admin

### Backend APIs
- **Chat API:** https://project-agent-chat-api-117860496175.us-central1.run.app
- **Inventory API:** https://project-agent-inventory-api-117860496175.us-central1.run.app
- **Documents API:** https://project-agent-documents-api-117860496175.us-central1.run.app
- **Admin API:** https://project-agent-admin-api-117860496175.us-central1.run.app
- **Upload API:** https://project-agent-upload-api-117860496175.us-central1.run.app

---

## 🔐 Authentication

**POC Setup:**
- **Who can access:** Any user with `@transparent.partners` email
- **Permissions:** All authenticated users have full access (admin + user features)
- **No role restrictions:** For POC, everyone can upload, delete, chat, and admin

**Portal Integration Ready:**
- Auth structure accepts JWT with `client_ids` and `project_ids` claims
- Ready for multi-tenant filtering when portal provides user context

---

## 🧪 QA Test Plan

### 1. Document Deletion Tests

#### A. Delete Single Document
**Location:** Admin Page → Inventory Tab

**Steps:**
1. Navigate to https://project-agent-web-117860496175.us-central1.run.app/admin
2. Click on "Inventory" tab
3. Find a document in the list
4. Click "Delete" button on the document row
5. Confirm deletion in modal

**Expected:** 
- Document removed from inventory list
- Firestore document deleted
- Success notification shown

**API Endpoint:** `DELETE /admin/documents/{doc_id}`

#### B. Bulk Delete Documents
**Location:** Admin Page → Inventory Tab

**Options to test:**
1. **Delete All Documents**
   - Click "Delete All" button
   - Confirm in modal
   - All documents removed from inventory

2. **Delete by Project**
   - Select project from filter
   - Click "Delete by Project" button
   - Only project documents deleted

3. **Delete by Client**
   - Select client from filter
   - Click "Delete by Client" button
   - Only client documents deleted

4. **Delete Specific Documents**
   - Select multiple documents via checkboxes
   - Click "Delete Selected" button
   - Only selected documents deleted

**API Endpoint:** `POST /admin/bulk-delete-documents`

**Request Body Options:**
```json
// Delete all
{"delete_all": true}

// Delete by project
{"project_id": "tp-main-project"}

// Delete by client
{"client_id": "transparent-partners"}

// Delete specific docs
{"document_ids": ["doc1", "doc2", "doc3"]}
```

---

### 2. Document Upload & Processing Tests

#### A. Single Document Upload
**Location:** Admin Page → Ingest Documents Tab

**Steps:**
1. Navigate to https://project-agent-web-117860496175.us-central1.run.app/admin
2. Click "Ingest Documents" tab
3. Click "Upload File" button
4. Select a PDF/DOCX file
5. Fill in metadata fields
6. Click "Upload"

**Expected:**
- File uploaded to GCS
- Document AI processes the file
- Metadata saved to Firestore
- Document appears in inventory
- Success notification shown

**API Endpoint:** `POST /upload`

#### B. Google Sheets Index Import
**Location:** Admin Page → Ingest Documents Tab

**Steps:**
1. Create a Google Sheet with these columns:
   - `SOW #`
   - `Deliverable`
   - `Responsible party`
   - `DeliverableID`
   - `Link`
   - `Notes`

2. Paste the Sheet URL in the form
3. Click "Import from Google Sheets"
4. Review parsed documents
5. Click "Ingest All"

**Expected:**
- Sheet parsed correctly
- All rows converted to documents
- Documents saved to Firestore
- Links accessible in inventory

**API Endpoint:** `POST /admin/analyze-document-index`

---

### 3. AI Chat with Document Retrieval Tests

#### A. Basic Chat Query
**Location:** Home Page → Chat Interface

**Steps:**
1. Navigate to https://project-agent-web-117860496175.us-central1.run.app
2. Enter a question related to your documents
3. Send the query

**Expected:**
- AI generates answer based on document content
- Citations shown with document references
- Page numbers and excerpts displayed
- Links to source documents work

**API Endpoint:** `POST /chat`

**Test Queries:**
- "What are the main deliverables?"
- "Who is responsible for [specific deliverable]?"
- "What is the timeline for [project phase]?"
- "Summarize the SOW requirements"

#### B. Citation Verification
**Steps:**
1. Send a query that should return specific documents
2. Click on a citation
3. Verify it opens the correct document
4. Check that the excerpt matches the source

**Expected:**
- Citations link to correct documents
- Excerpts are accurate
- Page numbers are correct

---

### 4. Google Drive Search Tests

#### A. Drive Search Integration
**Location:** Admin Page → Drive Search Tab

**Steps:**
1. Navigate to Admin → Drive Search
2. Enter search keywords
3. Review results
4. Click "Import" on a result

**Expected:**
- Search returns relevant Google Drive files
- File metadata displayed correctly
- Import adds file to inventory

**API Endpoint:** `POST /admin/search-drive`

---

### 5. Inventory & Filtering Tests

#### A. Inventory List View
**Location:** Admin Page → Inventory Tab

**Steps:**
1. Navigate to Admin → Inventory
2. Review document list
3. Test pagination (next/prev buttons)
4. Test sorting (by title, date, type)

**Expected:**
- All documents displayed
- Pagination works smoothly
- Sorting updates the list correctly

#### B. Filtering
**Test filters:**
- Document type filter (SOW, Timeline, Deliverable, Misc)
- Search by title/content
- Filter by upload date
- Filter by creator

**Expected:**
- Filters apply correctly
- Multiple filters work together (AND logic)
- Results update immediately

**API Endpoint:** `GET /inventory`

---

## 🔍 Known Limitations (POC)

1. **No multi-tenancy:** All users see all documents
2. **No role-based permissions:** Everyone has admin access
3. **Single client/project:** Designed for one organization
4. **Ingestion worker not deployed:** Background processing may be limited

---

## 🚀 Portal Integration Readiness

### Ready for Portal
✅ JWT-based authentication structure  
✅ User context with client_ids/project_ids  
✅ Document filtering functions in place  
✅ Clean separation of auth and data layers  

### Integration Points
1. **Auth Middleware** (`packages/shared/clients/auth.py`):
   - Replace `verify_google_token()` to decode portal JWT
   - Extract `client_ids`, `project_ids`, `role` from JWT claims

2. **Data Filtering** (`filter_documents_by_access()`):
   - Currently returns all documents
   - Add logic to filter by user's `client_ids` and `project_ids`

3. **Environment Variables:**
   - Portal will provide: `PORTAL_JWT_SECRET`, `PORTAL_API_URL`
   - Remove: `POC_CLIENT_ID`, `POC_PROJECT_ID`

---

## 🐛 Troubleshooting

### Service Health Checks
```bash
# Check all services
curl https://project-agent-chat-api-117860496175.us-central1.run.app/health
curl https://project-agent-admin-api-117860496175.us-central1.run.app/health
curl https://project-agent-inventory-api-117860496175.us-central1.run.app/health
curl https://project-agent-documents-api-117860496175.us-central1.run.app/health
curl https://project-agent-upload-api-117860496175.us-central1.run.app/health
```

### View Logs
```bash
# Chat API logs
gcloud logging read "resource.labels.service_name=project-agent-chat-api" --limit 50 --project=transparent-agent-test

# Admin API logs
gcloud logging read "resource.labels.service_name=project-agent-admin-api" --limit 50 --project=transparent-agent-test
```

---

## 📋 QA Checklist

### Admin Functionality
- [ ] Delete single document
- [ ] Bulk delete all documents
- [ ] Bulk delete by project
- [ ] Bulk delete by client
- [ ] Upload single document
- [ ] Import from Google Sheets
- [ ] Google Drive search
- [ ] View inventory with pagination
- [ ] Filter inventory by type/date/creator
- [ ] Sort inventory by columns

### User/Agent Functionality
- [ ] AI chat answers questions correctly
- [ ] Citations link to correct documents
- [ ] Document excerpts are accurate
- [ ] Chat response time < 5 seconds
- [ ] Vector search retrieves relevant docs
- [ ] Page navigation works in chat UI

### Data Integrity
- [ ] Deleted documents don't appear in chat
- [ ] Deleted documents don't appear in inventory
- [ ] Uploaded documents indexed properly
- [ ] Sheets import creates correct metadata
- [ ] Links/URIs work correctly

---

## 🎯 Next Steps

1. **Production QA** - Test all features above
2. **Fix Issues** - Address any bugs found
3. **Portal Design** - Plan multi-tenant architecture
4. **Migration** - Prepare for portal IAM integration


