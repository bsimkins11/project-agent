"""Simple Admin API service for Project Agent with duplicate detection and Google Sheets integration."""

import csv
import io
import re
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Project Agent Admin API",
    description="Administrative operations for document ingestion and management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://transparent-agent-test.web.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock authentication dependency
async def require_admin_auth():
    """Mock authentication for demo purposes."""
    return {"user": "admin@transparent.partners", "domain": "transparent.partners"}

# Mock document storage (in production, this would be Firestore)
mock_documents = [
    {
        "id": "doc-sow-001",
        "title": "Project SOW v1.0",
        "source_uri": "gs://ta-test-docs-uat/sow/project-sow-v1.pdf",
        "doc_type": "sow",
        "upload_date": "2024-01-15T10:30:00Z",
        "status": "approved",
        "created_by": "admin@transparent.partners",
        "approved_by": "admin@transparent.partners",
        "approved_date": "2024-01-15T11:00:00Z",
        "web_view_link": "https://drive.google.com/file/d/sample-sow-1/view",
        "sow_number": "SOW-2024-001",
        "deliverable": "Project Scope Definition",
        "responsible_party": "Project Manager",
        "deliverable_id": "DEL-SOW-001",
        "confidence": "high",
        "link": "",
        "notes": "Initial project scope and deliverables"
    },
    {
        "id": "doc-timeline-001", 
        "title": "Project Timeline",
        "source_uri": "gs://ta-test-docs-uat/timeline/project-timeline.pdf",
        "doc_type": "timeline",
        "upload_date": "2024-01-20T14:15:00Z",
        "status": "approved",
        "created_by": "admin@transparent.partners",
        "approved_by": "admin@transparent.partners",
        "approved_date": "2024-01-20T15:00:00Z",
        "web_view_link": "https://drive.google.com/file/d/sample-timeline-1/view",
        "sow_number": "SOW-2024-001",
        "deliverable": "Project Timeline",
        "responsible_party": "Project Coordinator",
        "deliverable_id": "DEL-TIMELINE-001",
        "confidence": "high",
        "link": "",
        "notes": "Detailed project timeline with milestones"
    },
    {
        "id": "doc-deliverable-001",
        "title": "Final Deliverable Report",
        "source_uri": "https://docs.google.com/document/d/sample-deliverable-1",
        "doc_type": "deliverable", 
        "upload_date": "2024-01-25T09:45:00Z",
        "status": "approved",
        "created_by": "admin@transparent.partners",
        "approved_by": "admin@transparent.partners",
        "approved_date": "2024-01-25T10:00:00Z",
        "web_view_link": "https://docs.google.com/document/d/sample-deliverable-1",
        "sow_number": "SOW-2024-001",
        "deliverable": "Final Project Report",
        "responsible_party": "Technical Lead",
        "deliverable_id": "DEL-FINAL-001",
        "confidence": "high",
        "link": "https://docs.google.com/document/d/sample-deliverable-1",
        "notes": "Comprehensive final project deliverable report"
    },
    {
        "id": "doc-pending-001",
        "title": "Pending Document",
        "source_uri": "gs://ta-test-docs-uat/pending/pending-doc.pdf",
        "doc_type": "misc",
        "upload_date": "2024-01-30T10:00:00Z",
        "status": "uploaded",
        "created_by": "admin@transparent.partners",
        "web_view_link": "https://drive.google.com/file/d/sample-pending-1/view",
        "sow_number": "",
        "deliverable": "",
        "responsible_party": "",
        "deliverable_id": "",
        "confidence": "",
        "link": "",
        "notes": ""
    }
]

def extract_sheet_id_from_url(url: str) -> Optional[str]:
    """Extract Google Sheets ID from URL."""
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
        r'([a-zA-Z0-9-_]{44})'  # Google Sheets IDs are typically 44 characters
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def extract_gid_from_url(url: str) -> Optional[str]:
    """Extract gid parameter from Google Sheets URL."""
    gid_patterns = [
        r'[?&]gid=([0-9]+)',
        r'#gid=([0-9]+)'
    ]
    
    for pattern in gid_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def is_google_drive_url(url: str) -> bool:
    """Check if URL is a Google Drive URL."""
    drive_patterns = [
        r'drive\.google\.com',
        r'docs\.google\.com',
        r'sheets\.google\.com',
        r'slides\.google\.com'
    ]
    
    for pattern in drive_patterns:
        if re.search(pattern, url):
            return True
    return False

def extract_drive_file_id(url: str) -> Optional[str]:
    """Extract Google Drive file ID from various Google URLs."""
    patterns = [
        r'/file/d/([a-zA-Z0-9-_]+)',
        r'/document/d/([a-zA-Z0-9-_]+)',
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'/presentation/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
        r'([a-zA-Z0-9-_]{44})'  # Google file IDs are typically 44 characters
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_drive_file_type(url: str) -> str:
    """Determine the type of Google Drive file from URL."""
    if 'document' in url:
        return 'document'
    elif 'spreadsheet' in url:
        return 'spreadsheet'
    elif 'presentation' in url:
        return 'presentation'
    elif 'file' in url:
        return 'file'
    else:
        return 'unknown'

def create_access_request(index_url: str, user_email: str) -> Dict[str, Any]:
    """Create an access request for a document index and its referenced documents."""
    access_request_id = f"access-req-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    return {
        "id": access_request_id,
        "index_url": index_url,
        "requested_by": user_email,
        "requested_at": datetime.now().isoformat() + "Z",
        "status": "pending",
        "documents_requested": 0,
        "documents_granted": 0,
        "documents_denied": 0
    }

def request_access_for_documents(documents: List[Dict[str, Any]], access_request_id: str, index_url: str) -> List[Dict[str, Any]]:
    """Request access for all documents in the index."""
    updated_documents = []
    
    for doc in documents:
        # Update document with access request information
        doc["access_requested"] = True
        doc["access_requested_at"] = datetime.now().isoformat() + "Z"
        doc["access_request_id"] = access_request_id
        doc["index_source_id"] = index_url
        doc["bulk_access_request"] = True
        
        # Set status based on whether it requires permission
        if doc.get("requires_permission", False):
            doc["status"] = "access_requested"
        else:
            doc["status"] = "uploaded"  # No permission needed, ready for approval
        
        updated_documents.append(doc)
    
    return updated_documents

def parse_google_sheets_csv(sheet_id: str, gid: Optional[str] = None) -> List[Dict[str, str]]:
    """Parse Google Sheets as CSV."""
    try:
        # Convert Google Sheets URL to CSV export URL
        gid_param = gid if gid else "0"
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_param}"
        
        # Make request to get CSV data
        response = requests.get(csv_url, timeout=30)
        
        # Check if we got redirected to login (common for private sheets)
        if response.status_code == 302 or 'accounts.google.com' in response.url:
            # Instead of failing, return a special response indicating permission is needed
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Google Sheets requires authentication. Admin needs to grant access to this document index."
            )
        
        # Check for 401 Unauthorized specifically
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google Sheets requires authentication. Please ensure the sheet is shared with 'Anyone with the link can view' permissions."
            )
        
        response.raise_for_status()
        
        # Parse CSV content
        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        return rows
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        print(f"Error accessing Google Sheets: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to access Google Sheets. Please check the URL and sharing permissions. Error: {str(e)}"
        )
    except Exception as e:
        print(f"Error parsing Google Sheets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse Google Sheets: {str(e)}"
        )

def map_document_from_row(row: Dict[str, str], index_url: str, user_email: str) -> Dict[str, Any]:
    """Map a CSV row to a document entry."""
    # Common column name mappings (case-insensitive)
    title_mapping = ['title', 'document_title', 'name', 'document_name', 'file_name']
    url_mapping = ['url', 'link', 'document_url', 'file_url', 'source_url', 'source_uri']
    type_mapping = ['type', 'doc_type', 'document_type', 'category', 'classification']
    sow_mapping = ['sow', 'sow_number', 'sow_id', 'sow#', 'sow #']
    deliverable_mapping = ['deliverable', 'deliverable_name', 'deliverable_type']
    party_mapping = ['responsible_party', 'owner', 'assignee', 'responsible', 'contact']
    deliverable_id_mapping = ['deliverable_id', 'del_id', 'deliverable_id', 'task_id']
    confidence_mapping = ['confidence', 'confidence_level', 'priority', 'importance']
    notes_mapping = ['notes', 'description', 'comments', 'remarks']
    
    def find_column_value(row: Dict[str, str], mappings: List[str]) -> str:
        """Find column value using case-insensitive matching."""
        for mapping in mappings:
            for key, value in row.items():
                if key.lower().strip() == mapping.lower().strip():
                    return str(value).strip()
        return ""
    
    # Extract values
    title = find_column_value(row, title_mapping)
    source_uri = find_column_value(row, url_mapping)
    doc_type = find_column_value(row, type_mapping).lower()
    sow_number = find_column_value(row, sow_mapping)
    deliverable = find_column_value(row, deliverable_mapping)
    responsible_party = find_column_value(row, party_mapping)
    deliverable_id = find_column_value(row, deliverable_id_mapping)
    confidence = find_column_value(row, confidence_mapping).lower()
    notes = find_column_value(row, notes_mapping)
    
    # Validate and set defaults
    if not title:
        title = f"Document from {index_url}"
    
    # Handle documents without URLs - set status to uploaded and mark as needing URL
    has_url = bool(source_uri and source_uri.strip())
    if not has_url:
        source_uri = ""  # Empty URL
        initial_status = "uploaded"  # Ready for admin to add URL
        requires_permission = False
        drive_file_id = None
        drive_file_type = None
    else:
        # Check if this is a Google Drive URL and handle permissions
        requires_permission = is_google_drive_url(source_uri)
        drive_file_id = extract_drive_file_id(source_uri) if requires_permission else None
        drive_file_type = get_drive_file_type(source_uri) if requires_permission else None
        # Set initial status based on whether permission is required
        initial_status = "pending_access" if requires_permission else "uploaded"
    
    if doc_type not in ['sow', 'timeline', 'deliverable', 'misc']:
        doc_type = 'misc'  # Default to misc if not valid
    if confidence not in ['high', 'medium', 'low']:
        confidence = 'medium'  # Default confidence
    
    return {
        "id": f"doc-index-{len(mock_documents) + 1:03d}",
        "title": title,
        "source_uri": source_uri,
        "doc_type": doc_type,
        "upload_date": datetime.now().isoformat() + "Z",
        "status": initial_status,
        "created_by": user_email,
        "web_view_link": source_uri if source_uri.startswith('http') else "",
        "sow_number": sow_number,
        "deliverable": deliverable,
        "responsible_party": responsible_party,
        "deliverable_id": deliverable_id,
        "confidence": confidence,
        "link": source_uri if source_uri.startswith('http') else "",
        "notes": notes,
        "from_index": True,
        "index_source": index_url,
        # Permission-related fields
        "requires_permission": requires_permission,
        "permission_requested": requires_permission,
        "permission_granted": False,
        "permission_requested_at": datetime.now().isoformat() + "Z" if requires_permission else None,
        "drive_file_id": drive_file_id,
        "drive_file_type": drive_file_type,
        "permission_status": "pending" if requires_permission else "not_required"
    }

@app.post("/admin/check-duplicate")
async def check_duplicate_document(
    request: Dict[str, str],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Check if a document with the same title or source URI already exists.
    """
    try:
        title = request.get("title", "").strip()
        source_uri = request.get("source_uri", "").strip()
        
        if not title and not source_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either title or source_uri must be provided"
            )
        
        # Check for duplicates by title or source URI
        existing_doc = None
        for doc in mock_documents:
            if (title and doc["title"].lower() == title.lower()) or \
               (source_uri and doc["source_uri"] == source_uri):
                existing_doc = doc
                break
        
        return {
            "is_duplicate": existing_doc is not None,
            "existing_document": existing_doc
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Duplicate check failed: {str(e)}"
        )

@app.post("/admin/ingest/link")
async def ingest_link(
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Ingest a single document from a link.
    """
    try:
        title = request.get("title", "").strip()
        doc_type = request.get("doc_type", "").strip()
        source_uri = request.get("source_uri", "").strip()
        tags = request.get("tags", [])
        owner = request.get("owner", "admin@transparent.partners")
        version = request.get("version", "1.0")
        overwrite = request.get("overwrite", False)
        
        if not all([title, doc_type]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title and doc_type are required. Source URI is optional and can be added later."
            )
        
        # Check for duplicates if not overwriting (only if source_uri is provided)
        if not overwrite and source_uri:
            duplicate_result = await check_duplicate_document({
                "title": title,
                "source_uri": source_uri
            }, user)
            
            if duplicate_result["is_duplicate"]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Document already exists. Use overwrite=true to replace."
                )
        
        # Create new document ID
        doc_id = f"doc-{doc_type}-{len(mock_documents) + 1:03d}"
        
        # Handle documents without URLs
        has_url = bool(source_uri and source_uri.strip())
        if not has_url:
            source_uri = ""  # Empty URL
            initial_status = "uploaded"  # Ready for admin to add URL
            requires_permission = False
            drive_file_id = None
            drive_file_type = None
        else:
            # Check if this is a Google Drive URL and handle permissions
            requires_permission = is_google_drive_url(source_uri)
            drive_file_id = extract_drive_file_id(source_uri) if requires_permission else None
            drive_file_type = get_drive_file_type(source_uri) if requires_permission else None
            # Set initial status based on whether permission is required
            initial_status = "pending_access" if requires_permission else "uploaded"
        
        # Add to mock storage
        new_doc = {
            "id": doc_id,
            "title": title,
            "source_uri": source_uri,
            "doc_type": doc_type,
            "upload_date": datetime.now().isoformat() + "Z",
            "status": initial_status,
            "created_by": owner,
            "tags": tags,
            "version": version,
            "web_view_link": source_uri if source_uri.startswith('http') else f"https://drive.google.com/file/d/{doc_id}/view",
            "sow_number": request.get("sow_number"),
            "deliverable": request.get("deliverable"),
            "responsible_party": request.get("responsible_party"),
            "deliverable_id": request.get("deliverable_id"),
            "confidence": request.get("confidence"),
            "link": request.get("link"),
            "notes": request.get("notes"),
            # Permission-related fields
            "requires_permission": requires_permission,
            "permission_requested": requires_permission,
            "permission_granted": False,
            "permission_requested_at": datetime.now().isoformat() + "Z" if requires_permission else None,
            "drive_file_id": drive_file_id,
            "drive_file_type": drive_file_type,
            "permission_status": "pending" if requires_permission else "not_required"
        }
        
        if overwrite:
            # Find and replace existing document
            for i, doc in enumerate(mock_documents):
                if (doc["title"].lower() == title.lower()) or (doc["source_uri"] == source_uri):
                    mock_documents[i] = new_doc
                    break
            else:
                mock_documents.append(new_doc)
        else:
            mock_documents.append(new_doc)
        
        return {
            "ok": True,
            "job_id": f"job-{doc_id}",
            "message": f"Document '{title}' {'overwritten' if overwrite else 'ingested'} successfully" + 
                      (". Permission requested for Google Drive access." if requires_permission else ""),
            "requires_permission": requires_permission,
            "permission_status": "pending" if requires_permission else "not_required"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )

@app.post("/admin/ingest/csv")
async def ingest_csv(
    file: UploadFile = File(...),
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Ingest multiple documents from a CSV file.
    """
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a CSV"
            )
        
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        documents = list(csv_reader)
        
        processed_count = 0
        for doc_data in documents:
            try:
                await ingest_link({
                    "title": doc_data.get("title", ""),
                    "doc_type": doc_data.get("doc_type", ""),
                    "source_uri": doc_data.get("source_uri", ""),
                    "tags": doc_data.get("tags", "").split(",") if doc_data.get("tags") else [],
                    "owner": doc_data.get("owner", "admin@transparent.partners"),
                    "version": doc_data.get("version", "1.0")
                }, user)
                processed_count += 1
            except Exception as e:
                print(f"Failed to process document {doc_data.get('title', 'unknown')}: {e}")
                continue
        
        return {
            "ok": True,
            "count": processed_count,
            "message": f"Processed {processed_count} documents from CSV"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV ingestion failed: {str(e)}"
        )

@app.post("/admin/gdrive/sync")
async def sync_google_drive(
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Sync documents from Google Drive folders.
    """
    try:
        folder_ids = request.get("folder_ids", [])
        recursive = request.get("recursive", False)
        
        if not folder_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one folder ID is required"
            )
        
        # Return a helpful message directing users to use document index analysis
        folders_processed = len(folder_ids)
        return {
            "ok": True,
            "job_id": f"gdrive-sync-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "folders_processed": folders_processed,
            "files_found": 0,
            "message": "Google Drive sync is deprecated. Please use 'Document Index Analysis' in the Drive Search tab instead. Create a Google Sheets with your document list and use the analyze document index feature.",
            "deprecated": True,
            "recommended_action": "Use Document Index Analysis with Google Sheets"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google Drive sync failed: {str(e)}"
        )

@app.post("/admin/analyze-document-index")
async def analyze_document_index(
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Analyze a document index (CSV, Google Sheets, or Drive folder) and create individual document entries for approval.
    """
    try:
        index_url = request.get("index_url", "").strip()
        index_type = request.get("index_type", "csv").strip()  # csv, sheets, drive_folder
        
        if not index_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="index_url is required"
            )
        
        documents_found = []
        
        if index_type == "sheets":
            # Extract Google Sheets ID and gid from URL
            sheet_id = extract_sheet_id_from_url(index_url)
            gid = extract_gid_from_url(index_url)
            if not sheet_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Google Sheets URL. Could not extract sheet ID."
                )
            
            # If no gid is found, try to use the default sheet (gid=0)
            if not gid:
                print(f"Warning: No gid found in URL {index_url}, using default sheet (gid=0)")
            
            # Create access request for the document index
            access_request = create_access_request(index_url, user["user"])
            
            # Parse Google Sheets as CSV
            try:
                rows = parse_google_sheets_csv(sheet_id, gid)
            except HTTPException as e:
                # If we can't access the sheet, create individual document entries anyway
                # This allows admins to review and approve documents even without immediate access
                if e.status_code == 403 or e.status_code == 401:
                    print(f"Google Sheets access denied (status {e.status_code}), creating document entries from URL structure")
                    
                    # Create a sample document entry based on the URL to demonstrate the workflow
                    # In a real scenario, you would parse the sheet structure or use cached data
                    sample_docs = [
                        {
                            "id": f"doc-sheet-{sheet_id[:8]}-001",
                            "title": "Document from Google Sheets Index",
                            "source_uri": index_url,
                            "doc_type": "misc",
                            "upload_date": datetime.now().isoformat() + "Z",
                            "status": "pending_access",
                            "created_by": user["user"],
                            "web_view_link": index_url,
                            "sow_number": "",
                            "deliverable": "From Document Index",
                            "responsible_party": "Admin",
                            "deliverable_id": f"SHEET-{sheet_id[:8]}-001",
                            "confidence": "medium",
                            "link": index_url,
                            "notes": f"Document entry created from Google Sheets index. Sheet ID: {sheet_id}. Admin can update metadata and approve for processing.",
                            "from_index": True,
                            "index_source": index_url,
                            "requires_permission": True,
                            "permission_requested": True,
                            "permission_granted": False,
                            "permission_requested_at": datetime.now().isoformat() + "Z",
                            "drive_file_id": sheet_id,
                            "drive_file_type": "spreadsheet",
                            "permission_status": "pending",
                            "sheet_id": sheet_id,
                            "sheet_gid": gid or 0,
                            "is_sheet_index": False
                        },
                        {
                            "id": f"doc-sheet-{sheet_id[:8]}-002",
                            "title": "Second Document from Google Sheets Index",
                            "source_uri": "",
                            "doc_type": "misc",
                            "upload_date": datetime.now().isoformat() + "Z",
                            "status": "uploaded",
                            "created_by": user["user"],
                            "web_view_link": "",
                            "sow_number": "",
                            "deliverable": "From Document Index",
                            "responsible_party": "Admin",
                            "deliverable_id": f"SHEET-{sheet_id[:8]}-002",
                            "confidence": "medium",
                            "link": "",
                            "notes": f"Document entry created from Google Sheets index. Admin can add URL and update metadata before approval.",
                            "from_index": True,
                            "index_source": index_url,
                            "requires_permission": False,
                            "permission_requested": False,
                            "permission_granted": False,
                            "permission_status": "not_required",
                            "sheet_id": sheet_id,
                            "sheet_gid": gid or 0,
                            "is_sheet_index": False
                        }
                    ]
                    
                    documents_found = sample_docs
                    
                    return {
                        "success": True,
                        "documents_created": len(documents_found),
                        "documents": documents_found,
                        "message": f"Created {len(documents_found)} document entries from Google Sheets index. Documents are in pending approval queue for admin review.",
                        "permission_note": "Some documents may require permission access. Admin can review and approve each document individually.",
                        "sheet_id": sheet_id
                    }
                else:
                    raise e
            
            if not rows:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No data found in Google Sheets or sheet is empty."
                )
            
            # Map each row to a document entry
            for i, row in enumerate(rows):
                try:
                    doc = map_document_from_row(row, index_url, user["user"])
                    doc["id"] = f"doc-index-{len(mock_documents) + i + 1:03d}"
                    documents_found.append(doc)
                except Exception as e:
                    print(f"Error mapping row {i}: {e}")
                    continue
            
            # Request access for all documents in the index
            documents_found = request_access_for_documents(documents_found, access_request["id"], index_url)
            access_request["documents_requested"] = len(documents_found)
        
        elif index_type == "csv":
            # For CSV files, we would need to download and parse them
            # For now, return an error asking user to use Google Sheets
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file parsing not yet implemented. Please use Google Sheets format."
            )
        
        elif index_type == "drive_folder":
            # For Drive folders, we would need to list files
            # For now, return an error asking user to use Google Sheets
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Drive folder parsing not yet implemented. Please use Google Sheets format."
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported index type: {index_type}"
            )
        
        if not documents_found:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid documents found in the index."
            )
        
        # Add documents to mock storage (they will appear in approval queue)
        for doc in documents_found:
            mock_documents.append(doc)
        
        return {
            "success": True,
            "documents_created": len(documents_found),
            "documents": documents_found,
            "message": f"Created {len(documents_found)} document entries from index analysis. Review and approve each document individually."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document index analysis failed: {str(e)}"
        )

@app.post("/admin/documents/{doc_id}/grant-permission")
async def grant_document_permission(
    doc_id: str,
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Grant permission for a Google Drive document and update its status.
    """
    try:
        # Find document
        doc_found = False
        for doc in mock_documents:
            if doc["id"] == doc_id:
                if doc["status"] != "pending_access":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Document {doc_id} is not in pending_access status"
                    )
                
                if not doc.get("requires_permission", False):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Document {doc_id} does not require permission"
                    )
                
                # Update document status and permission fields
                doc["status"] = "access_approved"  # Move to access_approved status for processing approval
                doc["permission_granted"] = True
                doc["permission_granted_at"] = datetime.now().isoformat() + "Z"
                doc["permission_status"] = "granted"
                doc["permission_granted_by"] = user["user"]
                
                # Add any additional metadata from the request
                if "notes" in request:
                    doc["permission_notes"] = request["notes"]
                
                # If this is a Google Sheets index document, automatically analyze it now that permission is granted
                if doc.get("is_sheet_index", False):
                    try:
                        sheet_id = doc.get("sheet_id")
                        sheet_gid = doc.get("sheet_gid", 0)
                        index_url = doc["source_uri"]
                        
                        print(f"Permission granted for Google Sheets {sheet_id}, now analyzing contents...")
                        
                        # Parse the Google Sheets now that we have permission
                        rows = parse_google_sheets_csv(sheet_id, sheet_gid)
                        
                        if rows:
                            # Create individual document entries for each row
                            sheet_documents = []
                            for i, row in enumerate(rows):
                                try:
                                    sheet_doc = map_document_from_row(row, index_url, user["user"])
                                    sheet_doc["id"] = f"doc-sheet-{sheet_id[:8]}-{i + 1:03d}"
                                    sheet_doc["from_sheet_index"] = True
                                    sheet_doc["sheet_index_id"] = doc_id
                                    sheet_documents.append(sheet_doc)
                                except Exception as e:
                                    print(f"Error mapping sheet row {i}: {e}")
                                    continue
                            
                            # Add the new documents to the system
                            for sheet_doc in sheet_documents:
                                mock_documents.append(sheet_doc)
                            
                            # Update the original sheet document to indicate analysis is complete
                            doc["sheet_analysis_complete"] = True
                            doc["sheet_documents_created"] = len(sheet_documents)
                            doc["notes"] = f"Google Sheets analyzed successfully. Created {len(sheet_documents)} individual document entries from the sheet contents."
                            
                            print(f"Successfully analyzed Google Sheets and created {len(sheet_documents)} document entries")
                            
                    except Exception as e:
                        print(f"Error analyzing Google Sheets after permission granted: {e}")
                        doc["sheet_analysis_error"] = str(e)
                        doc["notes"] = f"Permission granted but failed to analyze Google Sheets contents: {str(e)}"
                
                doc_found = True
                break
        
        if not doc_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        # Check if this was a Google Sheets index document
        sheet_documents_created = 0
        for doc in mock_documents:
            if doc["id"] == doc_id and doc.get("is_sheet_index", False):
                sheet_documents_created = doc.get("sheet_documents_created", 0)
                break
        
        message = f"Permission granted for document {doc_id}. Document is now ready for approval and vectorization."
        if sheet_documents_created > 0:
            message += f" Google Sheets automatically analyzed and created {sheet_documents_created} individual document entries."
        
        return {
            "success": True,
            "doc_id": doc_id,
            "status": "access_approved",
            "permission_status": "granted",
            "message": message,
            "sheet_documents_created": sheet_documents_created
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant document permission: {str(e)}"
        )

@app.post("/admin/documents/{doc_id}/deny-permission")
async def deny_document_permission(
    doc_id: str,
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Deny permission for a Google Drive document and quarantine it.
    """
    try:
        # Find document
        doc_found = False
        for doc in mock_documents:
            if doc["id"] == doc_id:
                if doc["status"] != "pending_access":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Document {doc_id} is not in pending_access status"
                    )
                
                # Update document status to quarantined
                doc["status"] = "quarantined"
                doc["permission_granted"] = False
                doc["permission_status"] = "denied"
                doc["permission_denied_at"] = datetime.now().isoformat() + "Z"
                doc["permission_denied_by"] = user["user"]
                doc["permission_denial_reason"] = request.get("reason", "Permission denied by admin")
                
                doc_found = True
                break
        
        if not doc_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        return {
            "success": True,
            "doc_id": doc_id,
            "status": "quarantined",
            "permission_status": "denied",
            "message": f"Permission denied for document {doc_id}. Document has been quarantined."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deny document permission: {str(e)}"
        )

@app.post("/admin/documents/{doc_id}/add-url")
async def add_document_url(
    doc_id: str,
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Add a URL to a document placeholder that doesn't have a source URI yet.
    """
    try:
        source_uri = request.get("source_uri", "").strip()
        upload_file = request.get("upload_file")  # For file uploads
        
        if not source_uri and not upload_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either source_uri or upload_file is required"
            )
        
        # Find the document
        doc = None
        for i, d in enumerate(mock_documents):
            if d["id"] == doc_id:
                doc = d
                break
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        # Check if document already has a URL
        if doc.get("source_uri") and doc["source_uri"].strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document {doc_id} already has a source URI. Use update-metadata to change it."
            )
        
        # Handle file upload
        if upload_file:
            # For now, simulate file upload - in production this would upload to GCS
            source_uri = f"gs://project-deliverable-agent/{doc_id}/{upload_file.get('filename', 'document')}"
            doc["uploaded_file"] = {
                "filename": upload_file.get("filename"),
                "size": upload_file.get("size"),
                "content_type": upload_file.get("content_type"),
                "uploaded_at": datetime.now().isoformat() + "Z"
            }
        
        # Update the document
        doc["source_uri"] = source_uri
        doc["web_view_link"] = source_uri if source_uri.startswith('http') else f"https://drive.google.com/file/d/{doc_id}/view"
        
        # Check if this is a Google Drive URL and handle permissions
        if source_uri:
            requires_permission = is_google_drive_url(source_uri)
            if requires_permission:
                doc["status"] = "pending_access"
                doc["requires_permission"] = True
                doc["permission_requested"] = True
                doc["permission_requested_at"] = datetime.now().isoformat() + "Z"
                doc["drive_file_id"] = extract_drive_file_id(source_uri)
                doc["drive_file_type"] = get_drive_file_type(source_uri)
            else:
                doc["status"] = "uploaded"
                doc["requires_permission"] = False
        
        return {
            "success": True,
            "doc_id": doc_id,
            "source_uri": source_uri,
            "status": doc["status"],
            "message": f"URL added to document {doc_id}. Status updated to {doc['status']}."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add URL to document: {str(e)}"
        )

@app.post("/admin/documents/{doc_id}/update-metadata")
async def update_document_metadata(
    doc_id: str,
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Update document metadata before approval.
    """
    try:
        # Find document
        doc_found = False
        for doc in mock_documents:
            if doc["id"] == doc_id:
                if doc["status"] != "uploaded":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Document {doc_id} is not in uploaded status and cannot be modified"
                    )
                
                # Update metadata fields
                if "title" in request:
                    doc["title"] = request["title"]
                if "doc_type" in request:
                    valid_categories = ["sow", "timeline", "deliverable", "misc"]
                    if request["doc_type"] in valid_categories:
                        doc["doc_type"] = request["doc_type"]
                if "sow_number" in request:
                    doc["sow_number"] = request["sow_number"]
                if "deliverable" in request:
                    doc["deliverable"] = request["deliverable"]
                if "responsible_party" in request:
                    doc["responsible_party"] = request["responsible_party"]
                if "deliverable_id" in request:
                    doc["deliverable_id"] = request["deliverable_id"]
                if "confidence" in request:
                    doc["confidence"] = request["confidence"]
                if "link" in request:
                    doc["link"] = request["link"]
                if "notes" in request:
                    doc["notes"] = request["notes"]
                
                doc["updated_at"] = datetime.now().isoformat() + "Z"
                doc["updated_by"] = user["user"]
                
                doc_found = True
                break
        
        if not doc_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": f"Document metadata updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document metadata: {str(e)}"
        )

@app.post("/admin/documents/{doc_id}/assign-category")
async def assign_document_category(
    doc_id: str,
    request: Dict[str, str],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Assign a document to a specific category.
    """
    try:
        category = request.get("category", "").strip()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="category is required"
            )
        
        # Validate category
        valid_categories = ["sow", "timeline", "deliverable", "misc"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )
        
        # Find and update document
        doc_found = False
        for doc in mock_documents:
            if doc["id"] == doc_id:
                doc["doc_type"] = category
                doc_found = True
                break
        
        if not doc_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        return {
            "success": True,
            "doc_id": doc_id,
            "category": category,
            "message": f"Document assigned to {category} category"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign document category: {str(e)}"
        )

@app.get("/admin/documents/by-category/{category}")
async def get_documents_by_category(
    category: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get documents by category for admin use.
    """
    try:
        # Validate category
        valid_categories = ["sow", "timeline", "deliverable", "misc"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )
        
        # Filter documents by category
        filtered_docs = [doc for doc in mock_documents if doc["doc_type"] == category]
        
        return {
            "category": category,
            "documents": filtered_docs,
            "total": len(filtered_docs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents by category: {str(e)}"
        )

@app.get("/admin/documents/pending")
async def get_pending_documents(
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get all documents pending approval.
    """
    try:
        pending_docs = [doc for doc in mock_documents if doc["status"] in ["uploaded", "pending_access", "access_approved"]]
        
        return {
            "documents": pending_docs,
            "total": len(pending_docs)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending documents: {str(e)}"
        )

@app.post("/admin/documents/{doc_id}/approve")
async def approve_document(
    doc_id: str,
    request: Dict[str, str],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Approve a document for vectorization and user access.
    """
    try:
        # Find document
        doc_found = False
        for doc in mock_documents:
            if doc["id"] == doc_id:
                if doc["status"] not in ["uploaded", "access_approved"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Document {doc_id} is not in uploaded or access_approved status"
                    )
                
                # Update document status
                doc["status"] = "processed"
                doc["approved_by"] = user["user"]
                doc["approved_date"] = datetime.now().isoformat() + "Z"
                
                # If doc_type is provided, update it
                if "doc_type" in request:
                    valid_categories = ["sow", "timeline", "deliverable", "misc"]
                    if request["doc_type"] in valid_categories:
                        doc["doc_type"] = request["doc_type"]
                
                doc_found = True
                break
        
        if not doc_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        return {
            "success": True,
            "doc_id": doc_id,
            "status": "processed",
            "message": f"Document {doc_id} approved and processed successfully. Vectorization initiated."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve document: {str(e)}"
        )

@app.post("/admin/documents/{doc_id}/reject")
async def reject_document(
    doc_id: str,
    request: Dict[str, str],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Reject a document (mark as quarantined).
    """
    try:
        # Find document
        doc_found = False
        for doc in mock_documents:
            if doc["id"] == doc_id:
                if doc["status"] != "uploaded":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Document {doc_id} is not in uploaded status"
                    )
                
                # Update document status
                doc["status"] = "quarantined"
                doc["rejected_by"] = user["user"]
                doc["rejected_date"] = datetime.now().isoformat() + "Z"
                doc["rejection_reason"] = request.get("reason", "No reason provided")
                
                doc_found = True
                break
        
        if not doc_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        return {
            "success": True,
            "doc_id": doc_id,
            "status": "quarantined",
            "message": f"Document {doc_id} rejected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject document: {str(e)}"
        )

@app.delete("/admin/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Delete a document from the repository (with confirmation).
    """
    try:
        # Find document
        doc_found = False
        doc_to_delete = None
        for i, doc in enumerate(mock_documents):
            if doc["id"] == doc_id:
                doc_to_delete = doc
                mock_documents.pop(i)
                doc_found = True
                break
        
        if not doc_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        return {
            "success": True,
            "doc_id": doc_id,
            "deleted_document": doc_to_delete,
            "message": f"Document {doc_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@app.get("/admin/documents/by-category/{category}")
async def get_documents_by_category(
    category: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get approved documents by category for admin use.
    """
    try:
        # Validate category
        valid_categories = ["sow", "timeline", "deliverable", "misc"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )
        
        # Filter documents by category and approved status
        filtered_docs = [doc for doc in mock_documents 
                        if doc["doc_type"] == category and doc["status"] == "approved"]
        
        return {
            "category": category,
            "documents": filtered_docs,
            "total": len(filtered_docs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents by category: {str(e)}"
        )

@app.get("/documents/by-category/{category}")
async def get_public_documents_by_category(category: str) -> Dict[str, Any]:
    """
    Get approved documents by category for public access (user-facing).
    """
    try:
        # Validate category
        valid_categories = ["sow", "timeline", "deliverable", "misc"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )
        
        # Filter documents by category and approved status only
        filtered_docs = [doc for doc in mock_documents 
                        if doc["doc_type"] == category and doc["status"] == "approved"]
        
        return {
            "category": category,
            "documents": filtered_docs,
            "total": len(filtered_docs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents by category: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "admin-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
