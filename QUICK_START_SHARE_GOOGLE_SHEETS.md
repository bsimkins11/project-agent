# Quick Start: Share Google Sheets with Agent

## Problem
You're seeing this error:
```
❌ Failed to analyze document index: Unable to access Google Sheets
```

## Solution (2 minutes)

### Step 1: Get the Service Account Email
1. In the Project Deliverable Agent admin panel, click **"Get Service Account Email"** or **"Service Account Info"**
2. Copy the email (looks like: `project-agent-drive-access@your-project.iam.gserviceaccount.com`)

### Step 2: Share Your Google Sheet
1. Open your Google Sheet
2. Click **Share** (top right corner)
3. Paste the service account email
4. Set permission to **Viewer**
5. Click **Send**

### Step 3: Try Again
1. Go back to the agent
2. Submit your Google Sheets URL again
3. ✅ Success!

## Visual Guide

```
┌─────────────────────────────────────┐
│  Your Google Sheet                  │
│                                     │
│  [Share] ← Click here              │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│  Share "Document Index"             │
│  ┌───────────────────────────────┐ │
│  │ Add people and groups         │ │
│  │ service-account@project.iam...│ │ ← Paste service account email
│  └───────────────────────────────┘ │
│  [Viewer ▼]                         │ ← Keep as "Viewer"
│                         [Send]      │ ← Click Send
└─────────────────────────────────────┘
```

## Why This Is Needed

The Project Deliverable Agent uses a **service account** to access Google Sheets on your behalf. Service accounts are like robot users - they need to be explicitly granted access to documents, just like any other user.

## You Only Need to Do This Once

Once you share a Google Sheet with the service account, it will have access forever (or until you remove it). You don't need to share it again.

## Troubleshooting

### I shared the sheet, but it still doesn't work
- Wait 30 seconds and try again (permissions can take a moment to propagate)
- Verify the service account email is exactly correct (copy-paste, don't type)
- Make sure you gave "Viewer" permission (not "Commenter" or "Editor")

### The service account email doesn't work
- Contact your system administrator
- Verify the service account is properly configured in Google Cloud Platform

### I don't see the "Service Account Info" button
- Make sure you're logged in as an admin
- Check that you're on the Admin Panel page
- Try refreshing the page

## Security Note

**The service account only has "Viewer" permission** - it can read your Google Sheets but cannot modify or delete them. This is the safest level of access.

## Alternative: Make Sheet Public (Not Recommended)

If you want to avoid sharing with the service account, you can make your sheet public:
1. Open Google Sheet → Share
2. Click "Change to anyone with the link"
3. Set to "Viewer"

⚠️ **Warning**: This makes your sheet visible to anyone with the link. Sharing with the service account is more secure.

