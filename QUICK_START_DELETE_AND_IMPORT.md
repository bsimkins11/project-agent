# Quick Start: Delete All & Import New Index

## 🎯 3 Simple Steps to Reset Your Documents

---

## Step 1: Delete All Existing Documents

### Option A: Via Web UI (Easiest - If Available)

1. Go to: **https://project-agent-web-117860496175.us-central1.run.app/admin**
2. Sign in with your @transparent.partners email
3. Click **"Inventory"** tab
4. Look for **"Delete All"** or **"Bulk Actions"** button
5. Confirm deletion

### Option B: Via Browser Console (Quick)

1. Go to: **https://project-agent-web-117860496175.us-central1.run.app/admin**
2. Open DevTools (Press `F12` or `Cmd+Option+I` on Mac)
3. Go to **Console** tab
4. Paste this code:

```javascript
// Delete all documents via API
fetch('https://project-agent-admin-api-117860496175.us-central1.run.app/admin/documents/bulk-delete', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    // The portal should auto-include your auth token
  },
  credentials: 'include',
  body: JSON.stringify({
    delete_all: true
  })
})
.then(r => r.json())
.then(data => {
  console.log('✅ Deletion complete!', data);
  alert(`Successfully deleted ${data.deleted_count} documents!`);
})
.catch(err => {
  console.error('❌ Error:', err);
  alert('Delete failed. Check console for details.');
});
```

5. Press Enter
6. Wait for confirmation message

---

## Step 2: Create Your Google Sheets Index

### A. Create the Sheet

1. Go to: **https://sheets.google.com**
2. Create new sheet
3. Name it: **"TP Project Document Index"**

### B. Add Column Headers (Exact spelling required!)

```
SOW #	Deliverable	Responsible party	DeliverableID	Link	Notes
```

### C. Fill in Your Documents

**Example:**

| SOW # | Deliverable | Responsible party | DeliverableID | Link | Notes |
|-------|-------------|-------------------|---------------|------|-------|
| SOW-001 | Project Charter | John Doe | DEL-CHARTER | https://docs.google.com/document/d/YOUR_DOC_ID/edit | Latest version |
| SOW-001 | Technical Spec | Jane Smith | DEL-SPEC | https://docs.google.com/document/d/YOUR_DOC_ID/edit | Approved |
| SOW-002 | Implementation Plan | Bob Jones | DEL-IMPL | https://docs.google.com/document/d/YOUR_DOC_ID/edit | Phase 1 |

### D. Share the Sheet

**Make it accessible:**
- Click "Share" button
- Set to "Anyone with the link can view"
- Or share with your service account email

### E. Copy the URL

Copy the full Sheet URL, e.g.:
```
https://docs.google.com/spreadsheets/d/1ABC123XYZ.../edit
```

---

## Step 3: Import Your New Index

1. **Navigate to Admin:**
   - https://project-agent-web-117860496175.us-central1.run.app/admin

2. **Go to "Ingest Documents" Tab**

3. **Find "Import from Google Sheets" section**

4. **Paste your Sheet URL**

5. **Click "Parse & Import"**

6. **Review** the parsed documents

7. **Click "Import All"**

---

## ✅ Verify Everything Works

### Check 1: Inventory
- Go to Admin → Inventory
- Should see all your new documents
- Count should match your sheet rows

### Check 2: AI Chat
- Go to home page
- Ask: "What are the deliverables?"
- Should cite your new documents

### Check 3: Document Links
- Click on a citation in chat
- Should open the Google Drive document
- Link should work

---

## 🚨 Troubleshooting

### "Delete All" button not found in UI?
**Use browser console method above (Option B)**

### Import fails?
**Check:**
- ✅ All 6 column headers spelled exactly right
- ✅ Sheet is shared/accessible
- ✅ Links are valid Google Drive URLs
- ✅ No duplicate DeliverableIDs
- ✅ Required fields not empty (SOW #, Deliverable, DeliverableID, Link)

### Documents don't appear in chat?
**Verify:**
- Documents show in Inventory with status "approved"
- Give it 30 seconds for indexing
- Refresh the page

---

## 🎉 You're All Set!

After completing these 3 steps:
- ✅ Old documents deleted
- ✅ New index imported
- ✅ AI chat working with your documents
- ✅ All features functional

**Your POC is ready for testing!**


