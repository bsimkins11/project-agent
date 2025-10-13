# Delete All Documents - POC Reset Guide

## 🗑️ How to Delete All Existing Documents

You have **3 easy options** to delete all documents:

---

### Option 1: Via Web UI (Recommended for POC)

**Steps:**
1. Go to https://project-agent-web-117860496175.us-central1.run.app/admin
2. Click "Inventory" tab
3. Look for "Delete All" or "Bulk Delete" button
4. Click it and confirm

*Note: UI needs to be updated with this button if not present*

---

### Option 2: Via API Call (Quick & Direct)

**Using curl:**

```bash
# Delete ALL documents
curl -X POST https://project-agent-admin-api-117860496175.us-central1.run.app/admin/documents/bulk-delete \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_GOOGLE_TOKEN" \
  -d '{"delete_all": true}'
```

**To get your Google token:**
1. Log into the web portal
2. Open browser DevTools (F12)
3. Go to Application/Storage → Local Storage
4. Find your auth token

---

### Option 3: Via Python Script (Most Reliable)

I can create a script that:
- Connects to Firestore directly
- Lists all documents
- Deletes them one by one with progress
- Shows count of deleted documents

---

## 📋 After Deletion: Import New Index

### Your New Template Fields:
Based on your requirements, use these columns in your Google Sheet:

| Column Name | Description | Required |
|------------|-------------|----------|
| **SOW #** | Statement of Work number | Yes |
| **Deliverable** | Deliverable title/name | Yes |
| **Responsible party** | Who owns this deliverable | No |
| **DeliverableID** | Unique identifier | Yes |
| **Link** | Google Drive link to document | Yes |
| **Notes** | Additional notes/context | No |

### Google Sheets Template

**Create a sheet with this structure:**

```
| SOW # | Deliverable | Responsible party | DeliverableID | Link | Notes |
|-------|-------------|-------------------|---------------|------|-------|
| SOW-001 | Project Plan | John Doe | DEL-001 | https://docs.google.com/... | Initial planning doc |
| SOW-001 | Technical Spec | Jane Smith | DEL-002 | https://docs.google.com/... | v2.0 spec |
| SOW-002 | Implementation Guide | Bob Johnson | DEL-003 | https://docs.google.com/... | Phase 1 guide |
```

### Import Process

1. **Create your Google Sheet** with the columns above
2. **Share the sheet:** Make it accessible to your service account
3. **Copy the Sheet URL**
4. **Go to Admin → Ingest Documents tab**
5. **Paste the Sheet URL**
6. **Click "Parse & Import"**

The system will:
- Parse each row
- Extract metadata from the columns
- Download content from the Google Drive links
- Index documents for AI chat
- Make them searchable

---

## 🎯 Which Option Do You Want?

1. **Web UI** - If the button exists, easiest option
2. **curl Command** - Quick, direct, just need your token
3. **Python Script** - I can create a robust deletion script for you

**Let me know and I'll help you execute!**

