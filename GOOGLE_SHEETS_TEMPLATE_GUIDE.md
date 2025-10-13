# Google Sheets Document Index Template
## POC Production Setup

---

## 📊 Template Structure

Create a Google Sheet with **exactly these column headers**:

| SOW # | Deliverable | Responsible party | DeliverableID | Link | Notes |
|-------|-------------|-------------------|---------------|------|-------|

---

## 📝 Column Definitions

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| **SOW #** | Text | ✅ Yes | Statement of Work identifier | `SOW-001`, `SOW-2024-Q1` |
| **Deliverable** | Text | ✅ Yes | Document title/deliverable name | `Project Charter`, `Technical Specification` |
| **Responsible party** | Text | No | Person or team responsible | `John Doe`, `Engineering Team` |
| **DeliverableID** | Text | ✅ Yes | Unique identifier for this deliverable | `DEL-001`, `CHARTER-2024` |
| **Link** | URL | ✅ Yes | Google Drive link to the actual document | `https://docs.google.com/document/d/...` |
| **Notes** | Text | No | Additional context or description | `Latest version as of Q4`, `Draft - review needed` |

---

## 📋 Example Template

**Copy this into your Google Sheet:**

```
SOW #	Deliverable	Responsible party	DeliverableID	Link	Notes
SOW-001	Project Charter	John Doe	DEL-CHARTER-001	https://docs.google.com/document/d/1ABC123/edit	Q4 2024 version
SOW-001	Technical Requirements	Jane Smith	DEL-TECH-001	https://docs.google.com/document/d/1DEF456/edit	Approved by stakeholders
SOW-002	Implementation Plan	Bob Johnson	DEL-IMPL-001	https://docs.google.com/document/d/1GHI789/edit	Phase 1 rollout
SOW-002	Testing Strategy	Alice Williams	DEL-TEST-001	https://docs.google.com/document/d/1JKL012/edit	UAT scenarios included
SOW-003	User Guide	Charlie Brown	DEL-GUIDE-001	https://docs.google.com/document/d/1MNO345/edit	Draft for review
```

---

## 🔗 Setting Up Your Template

### Step 1: Create the Google Sheet

1. Go to https://sheets.google.com
2. Create a new sheet
3. Name it: `Project Agent Document Index - [Your Project Name]`
4. Add the 6 column headers exactly as shown above

### Step 2: Fill in Your Documents

For each document you want to index:

1. **SOW #**: Enter the SOW reference number
   - Keep it consistent across related deliverables
   - Examples: `SOW-001`, `SOW-2024-Q1`, `SOW-ALPHA`

2. **Deliverable**: Clear, descriptive title
   - This becomes the document title in the system
   - Keep it concise but meaningful
   - Examples: `Project Charter`, `Technical Spec v2.0`

3. **Responsible party**: Owner's name (optional)
   - Can be a person or team
   - Used for organization and filtering

4. **DeliverableID**: Unique ID for this deliverable
   - Must be unique across all rows
   - Recommended format: `DEL-[TYPE]-[NUMBER]`
   - Examples: `DEL-CHARTER-001`, `DEL-SPEC-042`

5. **Link**: Google Drive document URL
   - Must be a valid Google Docs/Sheets/Slides URL
   - Document must be accessible by your service account
   - Full URL including `/edit` or `/view` at the end

6. **Notes**: Any additional context (optional)
   - Version notes
   - Status indicators
   - Review comments

### Step 3: Share the Sheet

**Important:** The sheet must be accessible to the service account

**Option A - Make it accessible to your organization:**
1. Click "Share" button
2. Change to "Anyone with the link can view"
3. Or share specifically with the service account email

**Option B - Domain-wide access:**
If you configured domain-wide delegation, it will automatically have access.

### Step 4: Get the Sheet URL

1. Copy the full URL from your browser
2. It should look like: `https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit`
3. You'll paste this into the Admin UI

---

## 🚀 Importing Your Index

### Via Admin UI

1. Navigate to: https://project-agent-web-117860496175.us-central1.run.app/admin
2. Click "Ingest Documents" tab
3. Find "Import from Google Sheets" section
4. Paste your Sheet URL
5. Click "Parse & Preview"
6. Review the parsed documents
7. Click "Import All"

### What Happens During Import

The system will:
1. ✅ Read your Google Sheet
2. ✅ Parse each row into a document
3. ✅ Map your columns to these fields:
   - `SOW #` → `sow_number` 
   - `Deliverable` → `title`
   - `Responsible party` → `responsible_party`
   - `DeliverableID` → `deliverable_id`
   - `Link` → `source_ref` (URI to the document)
   - `Notes` → `notes`
4. ✅ Set metadata:
   - `doc_type`: "deliverable" (or based on content)
   - `media_type`: "google_doc" / "google_sheet" / "pdf"
   - `status`: "approved" (ready for AI chat)
   - `project_id`: "tp-main-project" (POC)
   - `client_id`: "transparent-partners" (POC)
5. ✅ Save to Firestore
6. ✅ Make searchable in AI chat

---

## ✅ Verification

After import, verify your documents:

1. **Check Inventory:**
   - Go to Admin → Inventory
   - All documents should appear
   - Metadata should be correct

2. **Test AI Chat:**
   - Go to home page
   - Ask: "What are the deliverables?"
   - Should see your documents in citations

3. **Test Document Links:**
   - Click on a citation
   - Should open the Google Drive document

---

## 🔧 Template Validation

**Before importing, check:**
- ✅ All required columns present (SOW #, Deliverable, DeliverableID, Link)
- ✅ No duplicate DeliverableIDs
- ✅ All Links are valid Google Drive URLs
- ✅ Sheet is shared/accessible
- ✅ No empty required fields

**Common Issues:**
- ❌ Missing column headers → Import will fail
- ❌ Duplicate DeliverableIDs → Second one will overwrite first
- ❌ Invalid Links → Document won't be accessible
- ❌ Sheet not shared → Permission denied error

---

## 📞 Need Help?

If import fails, check:
1. Service account has access to the sheet
2. All required columns are spelled exactly as shown
3. Links are valid and accessible
4. No special characters in DeliverableIDs


