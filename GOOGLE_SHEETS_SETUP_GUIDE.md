# Google Sheets Document Index Setup Guide

## Overview
This guide helps you set up Google Sheets for document index analysis in the Project Deliverable Agent. Users can paste a Google Sheets URL to automatically create document entries for review and approval.

## Required Google Sheets Format

### Expected Column Headers
Your Google Sheets should include these columns (exact names or variations):

| Column Name | Description | Example |
|-------------|-------------|---------|
| **SOW #** | Statement of Work number | "SOW-2024-001" |
| **Deliverable** | Deliverable description | "Project Charter" |
| **Responsible party** | Person/team responsible | "John Smith" |
| **DeliverableID** | Unique deliverable identifier | "DEL-001" |
| **Link** | Document URL or Google Drive link | "https://drive.google.com/..." |

### Optional Columns
- **Title** or **Document Title** - Document name
- **Type** or **Doc Type** - Document category (sow, timeline, deliverable, misc)
- **Notes** or **Description** - Additional information

## Step-by-Step Setup

### 1. Create Your Google Sheets
1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Add the column headers in the first row
4. Fill in your document information

### 2. Share with Service Account (REQUIRED)

**Important**: You must share your Google Sheet with the service account for the agent to access it.

#### Getting the Service Account Email
1. In the Project Deliverable Agent, go to the Admin Panel
2. Look for the "Service Account Info" section or button
3. Copy the service account email (it looks like: `project-agent-drive-access@your-project.iam.gserviceaccount.com`)

#### Sharing Your Google Sheet
1. Open your Google Sheet
2. Click the **Share** button (top right corner)
3. Paste the service account email
4. Set permission to **Viewer**
5. Click **Send**

**Note**: You only need to share once. The service account will retain access for all future operations.

### 3. Get Your Sheet URL
1. Copy the URL from your browser's address bar
2. The URL should look like:
   ```
   https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit#gid=0
   ```

### 4. Test Your Sheet
Before submitting to the system, verify:
- ✅ Sheet has been shared with the service account
- ✅ Sheet contains data (not empty)
- ✅ Column headers are in the first row
- ✅ URL is complete and valid

## Common Issues and Solutions

### Issue: "Failed to analyze document index"
**Possible Causes:**

1. **🔒 Service account doesn't have access (MOST COMMON)**
   - **Error message**: "Unable to access Google Sheets. Please share the document with the service account."
   - **Solution**: 
     - Get the service account email from the Admin Panel (look for "Service Account Info")
     - Open your Google Sheet
     - Click "Share" and add the service account email with "Viewer" permission
     - Try again
   
2. **Empty or no data in sheet**
   - Solution: Add at least one row of data below headers
   
3. **Invalid Google Sheets URL**
   - Solution: Copy the complete URL from browser address bar
   
4. **Sheet doesn't exist or was deleted**
   - Solution: Verify the sheet exists and URL is correct

### Issue: "No data found in Google Sheets"
**Solutions:**
1. Add data rows below the header row
2. Check that headers are in row 1
3. Ensure data is not in a different sheet/tab

## Sample Google Sheets Layout

```
| SOW #      | Deliverable        | Responsible party | DeliverableID | Link                    |
|------------|--------------------|--------------------|---------------|-------------------------|
| SOW-001    | Project Charter    | John Smith        | DEL-001       | https://drive.google.com/... |
| SOW-001    | Requirements Doc   | Jane Doe          | DEL-002       | https://drive.google.com/... |
| SOW-002    | Timeline           | Project Team      | DEL-003       | https://docs.google.com/... |
```

## Best Practices

1. **Use consistent column names** - The system recognizes variations, but consistency helps
2. **Include complete URLs** - Full Google Drive or document links work best
3. **Add meaningful titles** - If no title column, the system will create titles from other fields
4. **Keep data clean** - Avoid empty rows between data entries

## Troubleshooting Checklist

When submitting a Google Sheets URL, verify:
- [ ] Sheet contains data rows (not just headers)
- [ ] URL is complete and valid
- [ ] Headers are in row 1
- [ ] At least one required column exists (SOW #, Deliverable, Link, etc.)
- [ ] Google Drive API access is properly configured

## Need Help?

If you continue to experience issues:
1. Double-check all items in the troubleshooting checklist
2. Try creating a simple test sheet with just a few rows
3. Verify the URL works by opening it in an incognito browser window
4. Contact your system administrator for additional support

## Example Working URLs

These are examples of properly formatted Google Sheets URLs:
```
https://docs.google.com/spreadsheets/d/1YXBh6LHITAPmmwNinWVgYMJhJhqVwOPQj3T0h2PI-UU/edit#gid=0
https://docs.google.com/spreadsheets/d/1ABC123XYZ789/edit
https://docs.google.com/spreadsheets/d/1DEF456GHI012/edit?usp=sharing
```

Remember: The key is ensuring the sheet contains data and proper Google Drive API access is configured!
