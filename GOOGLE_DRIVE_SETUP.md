# Google Drive Access Setup Guide

## Overview

The Project Deliverable Agent uses **Admin-Controlled Document Access**. Admins manually select documents from Google Drive folders they have access to, and these documents are queued for approval before vectorization.

## 🔧 Simple Setup Process

### 1. Admin Access Required

- Admin must be logged into the Project Deliverable Agent
- Admin must have access to the Google Drive folders they want to search
- No service account configuration needed

### 2. Document Selection Process

1. **Admin goes to Drive Search tab**
2. **Pastes Google Drive folder URL** (e.g., `https://drive.google.com/drive/folders/1ABC123def456`)
3. **System shows documents** in that folder
4. **Admin selects documents** to add to approval queue
5. **Selected documents** are queued for admin approval
6. **Approved documents** get vectorized and become searchable

### 3. Supported Drive URLs

The system accepts:
- Full Google Drive folder URLs: `https://drive.google.com/drive/folders/1ABC123def456`
- Folder IDs only: `1ABC123def456`
- Automatically extracts folder ID from URLs

## 🔐 Security & Permissions

### Admin Requirements
- Admin must be logged into the Project Deliverable Agent
- Admin must have access to Google Drive folders they want to search
- Admin controls which documents get added to the system
- All documents require admin approval before vectorization

### No Complex Setup Required
- No service account keys needed
- No domain-wide delegation required
- No OAuth token management
- Uses admin's existing Google Drive access

## 📁 Supported File Types

The system can process these Drive file types:
- **PDF**: `application/pdf`
- **Google Docs**: `application/vnd.google-apps.document`
- **Google Sheets**: `application/vnd.google-apps.spreadsheet`
- **Word**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Text**: `text/plain`
- **Markdown**: `text/markdown`

## 🔄 Complete Workflow

1. **Admin logs into Project Deliverable Agent**
2. **Admin goes to Drive Search tab**
3. **Admin pastes Drive folder URL**
4. **System shows available documents**
5. **Admin selects documents** to add
6. **Documents are queued** for approval
7. **Admin approves documents** in Document Approval tab
8. **Approved documents** are downloaded and processed
9. **Text is extracted** and vectorized
10. **Documents become searchable** in the agent

## 🚀 Testing the System

### 1. Test Drive Search
1. Go to Admin Panel → Drive Search
2. Paste a Google Drive folder URL you have access to
3. Click "Search Documents"
4. Verify documents are listed

### 2. Test Document Addition
1. Select documents from the search results
2. Click "Add Selected to Approval Queue"
3. Go to Document Approval tab
4. Approve documents for processing

## 🛠️ Troubleshooting

### Common Issues

1. **"No documents found"**:
   - Verify you have access to the Drive folder
   - Check the folder URL is correct
   - Ensure the folder contains files (not just subfolders)

2. **"Invalid folder URL"**:
   - Use full Google Drive URL: `https://drive.google.com/drive/folders/1ABC123def456`
   - Or just the folder ID: `1ABC123def456`

3. **"Documents not processing"**:
   - Check Document Approval tab
   - Ensure documents are approved
   - Verify document indexing worker is running

## 📋 Simple Checklist

- [ ] Admin has access to Google Drive folders
- [ ] Drive Search functionality working
- [ ] Documents can be selected and queued
- [ ] Document Approval system working
- [ ] Approved documents get vectorized
- [ ] Documents become searchable in chat

## 🎯 Benefits of This Approach

- **Simple Setup**: No complex authentication required
- **Admin Control**: Full control over which documents are added
- **Security**: Uses admin's existing Drive permissions
- **Flexibility**: Works with any Drive folder admin has access to
- **Transparency**: Clear approval workflow for all documents
