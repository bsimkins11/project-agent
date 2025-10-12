# Document Index Template - Google Sheets Format

## 📋 Required Template Fields

Use these **exact column headers** in your Google Sheets document index:

| Column Header | Field Type | Required | Description | Example |
|--------------|------------|----------|-------------|---------|
| **SOW #** | Text | Optional | Statement of Work number | CHR-SOW-001 |
| **Deliverable** | Text | Optional | Deliverable description | Phase 1 Requirements Doc |
| **Responsible party** | Text | Optional | Person or team responsible | John Doe / Engineering Team |
| **DeliverableID** | Text | Optional | Unique deliverable identifier | DEL-001 |
| **Link** | URL | **Required** | Google Drive document link | https://docs.google.com/document/d/... |
| **Notes** | Text | Optional | Additional notes or comments | Draft version, needs review |

### **Additional Recommended Columns:**

| Column Header | Description | Example |
|--------------|-------------|---------|
| **Title** | Document title (auto-generated if missing) | Requirements Document |
| **Type** | Document category: sow, timeline, deliverable, misc | deliverable |

---

## 📝 Google Sheets Template

### **Create a New Sheet with These Headers:**

```
| SOW # | Deliverable | Responsible party | DeliverableID | Link | Notes | Title | Type |
|-------|-------------|-------------------|---------------|------|-------|-------|------|
```

### **Example Rows:**

```
| SOW # | Deliverable | Responsible party | DeliverableID | Link | Notes | Title | Type |
|-------|-------------|-------------------|---------------|------|-------|-------|------|
| CHR-001 | Requirements Doc | John Doe | DEL-001 | https://docs.google.com/document/d/abc123 | Initial draft | Product Requirements | sow |
| CHR-001 | Timeline | Jane Smith | DEL-002 | https://docs.google.com/spreadsheets/d/xyz789 | Q1 2024 | Project Timeline | timeline |
| CHR-002 | Deliverable Report | Engineering Team | DEL-003 | https://drive.google.com/file/d/def456 | Final version | Phase 1 Report | deliverable |
| CHR-002 | Meeting Notes | Project Manager | DEL-004 | https://docs.google.com/document/d/ghi789 | Weekly sync | Team Meeting Notes | misc |
```

---

## 🔍 Field Mapping Details

### **How Fields Are Used:**

#### **SOW #** (Statement of Work Number)
- **Field:** `sow_number`
- **Purpose:** Link document to specific SOW or contract
- **Searchable:** Yes
- **Example:** "CHR-SOW-001", "PROJECT-2024-Q1"

#### **Deliverable**
- **Field:** `deliverable`
- **Purpose:** Description of what this document represents
- **Searchable:** Yes
- **Example:** "Phase 1 Requirements", "Q2 Timeline"

#### **Responsible party**
- **Field:** `responsible_party`
- **Purpose:** Who owns or is responsible for this deliverable
- **Searchable:** Yes
- **Example:** "John Doe", "Engineering Team", "Product Manager"

#### **DeliverableID**
- **Field:** `deliverable_id`
- **Purpose:** Unique identifier for tracking deliverables
- **Searchable:** Yes
- **Example:** "DEL-001", "ITEM-2024-001"

#### **Link**
- **Field:** `source_uri` and `link`
- **Purpose:** URL to the actual Google Drive document
- **Required:** YES - This is the primary document reference
- **Formats Supported:**
  - Google Docs: `https://docs.google.com/document/d/{id}`
  - Google Sheets: `https://docs.google.com/spreadsheets/d/{id}`
  - Google Slides: `https://docs.google.com/presentation/d/{id}`
  - Google Drive: `https://drive.google.com/file/d/{id}`

#### **Notes**
- **Field:** `notes`
- **Purpose:** Additional context, status, or comments
- **Searchable:** Yes
- **Example:** "Draft version", "Needs review", "Approved by PM"

---

## 🎯 Column Header Variations (All Supported)

The system supports multiple header formats for flexibility:

### **SOW # Field:**
- ✅ `SOW #`
- ✅ `sow_number`
- ✅ `SOW Number`

### **Deliverable Field:**
- ✅ `Deliverable`
- ✅ `deliverable`

### **Responsible party Field:**
- ✅ `Responsible party`
- ✅ `Responsible Party`
- ✅ `responsible_party`

### **DeliverableID Field:**
- ✅ `DeliverableID`
- ✅ `Deliverable ID`
- ✅ `deliverable_id`

### **Link Field:**
- ✅ `Link`
- ✅ `link`
- ✅ `URL`

### **Notes Field:**
- ✅ `Notes`
- ✅ `notes`

**Recommendation:** Use the exact capitalization shown in the template for clarity.

---

## 🚀 How to Use the Template

### **Step 1: Create Google Sheet**
1. Go to Google Sheets
2. Create new spreadsheet
3. Name it: "Project Document Index - [Project Name]"

### **Step 2: Add Headers (Row 1)**
```
SOW # | Deliverable | Responsible party | DeliverableID | Link | Notes | Title | Type
```

### **Step 3: Add Document Rows**
Fill in each row with a document:
- **Required:** Link (must be a Google Drive URL)
- **Optional but Recommended:** All other fields

### **Step 4: Import to Project Agent**
1. Copy the Google Sheets URL
2. Go to Admin → Projects
3. Create or edit project
4. Paste Google Sheets URL in "Document Index URL"
5. Click "Import Documents"

---

## 📊 Data Flow

```
Google Sheets Template
  ↓
Column Headers (SOW #, Deliverable, etc.)
  ↓
Parse Sheets API
  ↓
Map to Document Fields
  ↓
Create DocumentMetadata
  ↓
Save to Firestore
  ↓
Documents appear in Inventory
```

---

## ✅ Validation Rules

### **Required Validations:**
- ✅ **Link field must be present** (can be empty but column must exist)
- ✅ Link must be valid Google Drive URL if provided
- ✅ At least one of Title or Link must have a value

### **Optional Validations:**
- Type should be: `sow`, `timeline`, `deliverable`, or `misc` (defaults to `misc`)
- All other fields are optional

### **Auto-Generated Fields:**
- `id`: Generated automatically (format: `doc-sheet-{sheetId}-{rowNum}`)
- `created_at`: Current timestamp
- `created_by`: User who imported
- `project_id`: Assigned project
- `client_id`: Assigned client
- `from_sheet_index`: Set to `true`

---

## 🎨 Example Google Sheet

**Sheet Name:** CHR MarTech Document Index

| SOW # | Deliverable | Responsible party | DeliverableID | Link | Notes | Title | Type |
|-------|-------------|-------------------|---------------|------|-------|-------|------|
| CHR-001 | Requirements Document | Product Team | CHR-DEL-001 | https://docs.google.com/document/d/1abc...xyz | Version 2.0 approved | Product Requirements | sow |
| CHR-001 | Project Timeline | PM | CHR-DEL-002 | https://docs.google.com/spreadsheets/d/2def...uvw | Q1 2024 timeline | Timeline 2024 Q1 | timeline |
| CHR-002 | Technical Spec | Engineering | CHR-DEL-003 | https://docs.google.com/document/d/3ghi...rst | Ready for review | Tech Specification | deliverable |
| CHR-002 | Architecture Diagram | Solutions Architect | CHR-DEL-004 | https://drive.google.com/file/d/4jkl...mno | Final version | System Architecture | deliverable |
| CHR-003 | Meeting Notes | Scrum Master | CHR-DEL-005 | https://docs.google.com/document/d/5pqr...stu | Weekly standup | Sprint 5 Notes | misc |

---

## 💡 Pro Tips

### **Tip 1: Use Consistent SOW Numbers**
Group documents by SOW number for easy filtering:
- All CHR-001 documents together
- All CHR-002 documents together

### **Tip 2: Use Descriptive Deliverable IDs**
Format: `{PROJECT}-DEL-{NUMBER}`
- CHR-DEL-001, CHR-DEL-002, etc.
- Makes tracking easier across projects

### **Tip 3: Be Specific in Responsible Party**
Use full names or team names:
- ✅ "John Doe (Product)"
- ✅ "Engineering Team"
- ❌ "JD" (too vague)

### **Tip 4: Add Meaningful Notes**
Notes help with context:
- "Approved by client on 2024-01-15"
- "Draft - needs stakeholder review"
- "Final version - signed off"

### **Tip 5: Keep Links Updated**
If documents move:
1. Update the Link column in your sheet
2. Re-import to Project Agent
3. System will update references

---

## 🔧 Current System Support

### **Already Implemented:** ✅
The system **already supports** all 5 fields you specified:
- ✅ SOW # → `sow_number`
- ✅ Deliverable → `deliverable`
- ✅ Responsible party → `responsible_party`
- ✅ DeliverableID → `deliverable_id`
- ✅ Link → `link` / `source_uri`
- ✅ Notes → `notes`

### **Parsing Code Location:**
- File: `services/api/admin/app.py`
- Lines: 860-865
- Function: `analyze_document_index()`

---

## 📖 Quick Start

1. **Copy this template to Google Sheets**
2. **Fill in your documents**
3. **Share sheet** (or make it accessible to your service account)
4. **Import via Admin → Projects**
5. **Documents appear in Inventory** with all metadata

---

## 🎯 Your 5-Field Template is Ready!

**Column Headers to Use:**
```
SOW # | Deliverable | Responsible party | DeliverableID | Link | Notes
```

**System Status:** ✅ Fully supported, production-ready!

**Next Step:** Create your Google Sheet using this template!

