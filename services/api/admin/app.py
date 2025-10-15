"""Production Admin API service for Project Agent with service account integration."""

import csv
import io
import re
import requests
import logging
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import secretmanager
from google.cloud import firestore
import sys

# Add project root to Python path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from packages.shared.schemas.document import (
    DocumentMetadata, DocumentStatus, DocType, MediaType, 
    DocumentCategory, DocumentSubcategory, ClassificationInfo
)
from packages.shared.schemas.inventory import InventoryRequest, InventoryResponse, InventoryFilters, InventoryItem
from packages.shared.schemas.admin import (
    AccessRequestStatus, DocumentAccessRequest, BulkAccessRequest, 
    AccessRequestAction, AdminAction
)
from packages.shared.clients.auth import require_domain_auth as _require_domain_auth, get_user_oauth_credentials
from packages.shared.clients.sheets import HybridSheetsClient

app = FastAPI(
    title="Project Agent Admin API",
    description="Administrative operations for document ingestion and management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://transparent-agent-test.web.app", "https://project-agent-web-117860496175.us-central1.run.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Drive Service Account Integration
class GoogleDriveServiceAccount:
    """Service account for accessing Google Drive and Sheets API."""
    
    def __init__(self):
        """Initialize service account with credentials from Secret Manager."""
        try:
            # Load credentials from Google Secret Manager
            project_id = os.getenv("GCP_PROJECT", "transparent-agent-test")
            secret_client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{project_id}/secrets/service-account-key/versions/latest"
            
            response = secret_client.access_secret_version(request={"name": secret_name})
            secret_payload = response.payload.data.decode("UTF-8")
            credentials_info = json.loads(secret_payload)
            
            # Store service account email for sharing instructions
            self.service_account_email = credentials_info.get("client_email", "")
            
            # Create credentials
            SCOPES = [
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/spreadsheets.readonly'
            ]
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=SCOPES
            )
            
            # Build service clients
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            
            logger.info(f"Service account credentials initialized successfully: {self.service_account_email}")
        except Exception as e:
            logger.error(f"Failed to initialize service account: {e}")
            self.credentials = None
            self.drive_service = None
            self.sheets_service = None
            self.service_account_email = ""
    
    def parse_google_sheets(self, sheet_id: str, gid: int = 0) -> List[Dict[str, Any]]:
        """Parse Google Sheets using service account."""
        try:
            if not self.sheets_service:
                raise Exception("Sheets service not initialized")
            
            # Convert gid to int if it's a string
            if isinstance(gid, str):
                gid = int(gid) if gid.isdigit() else 0
            
            # Get sheet name from GID
            sheet_name = "Sheet1"  # Default
            if gid > 0:
                spreadsheet = self.sheets_service.spreadsheets().get(
                    spreadsheetId=sheet_id
                ).execute()
                
                for sheet in spreadsheet.get('sheets', []):
                    sheet_props = sheet.get('properties', {})
                    if sheet_props.get('sheetId') == gid:
                        sheet_name = sheet_props.get('title', f'Sheet{gid}')
                        break
            
            # Get sheet data
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=sheet_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return []
            
            # Convert to list of dicts
            headers = values[0]
            rows = []
            for row_values in values[1:]:
                row_dict = {}
                for i, header in enumerate(headers):
                    row_dict[header] = row_values[i] if i < len(row_values) else ""
                rows.append(row_dict)
            
            return rows, sheet_name
        except Exception as e:
            logger.error(f"Error parsing Google Sheets with service account: {e}")
            raise

# Initialize service account
google_drive_service = GoogleDriveServiceAccount()

# Firestore client for production
class FirestoreClient:
    """Firestore client for document metadata storage."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT", "transparent-agent-test")
        self.db = firestore.Client(project=self.project_id)
    
    async def save_document(self, metadata: DocumentMetadata) -> str:
        """Save document metadata to Firestore."""
        try:
            doc_ref = self.db.collection("documents").document(metadata.id)
            doc_ref.set(metadata.dict())
            logger.info(f"Saved document {metadata.id} to Firestore")
            return metadata.id
        except Exception as e:
            logger.error(f"Error saving document to Firestore: {e}")
            raise
    
    async def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Get document metadata from Firestore."""
        try:
            doc_ref = self.db.collection("documents").document(doc_id)
            doc = doc_ref.get()
            if doc.exists:
                return DocumentMetadata(**doc.to_dict())
            return None
        except Exception as e:
            logger.error(f"Error getting document from Firestore: {e}")
            return None
    
    async def query_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Query documents by category - only return processed documents."""
        try:
            docs_ref = self.db.collection("documents")
            query = docs_ref.where("doc_type", "==", category).where("status", "==", "document_processed")
            docs = query.stream()
            
            documents = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["id"] = doc.id
                documents.append(doc_data)
            
            return documents
        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            return []

firestore_client = FirestoreClient()

# POC: All authenticated @transparent.partners users have full admin access
# Portal integration: Will use proper role-based permissions from JWT
require_admin_auth = _require_domain_auth  # Alias for consistency

# Mock document storage for backwards compatibility
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

@app.get("/admin/classification-options")
async def get_classification_options(
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get all available document classification options.
    """
    try:
        return {
            "doc_types": [{"value": dt.value, "label": dt.value.replace("_", " ").title()} for dt in DocType],
            "categories": [{"value": cat.value, "label": cat.value.replace("_", " ").title()} for cat in DocumentCategory],
            "subcategories": [{"value": sub.value, "label": sub.value.replace("_", " ").title()} for sub in DocumentSubcategory]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get classification options: {str(e)}"
        )

@app.get("/admin/service-account-info")
async def get_service_account_info(
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get service account information for sharing Google Sheets and Drive documents.
    Returns the service account email that users need to share documents with.
    """
    return {
        "service_account_email": google_drive_service.service_account_email,
        "instructions": {
            "google_sheets": [
                "1. Open your Google Sheet",
                "2. Click the 'Share' button in the top right",
                f"3. Add '{google_drive_service.service_account_email}' as a viewer",
                "4. Set permission to 'Viewer'",
                "5. Click 'Send'",
                "6. Return to the agent and try analyzing the document again"
            ],
            "google_drive": [
                "1. Navigate to the document or folder in Google Drive",
                "2. Right-click and select 'Share'",
                f"3. Add '{google_drive_service.service_account_email}' as a viewer",
                "4. Set permission to 'Viewer'",
                "5. Click 'Send'",
                "6. Return to the agent and try again"
            ]
        },
        "note": "You only need to share documents once. The service account will retain access for all future operations."
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

@app.post("/admin/test-analyze-document-index")
async def test_analyze_document_index(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    TEST ENDPOINT: Analyze document index without authentication.
    This is for testing the Google Sheets access functionality.
    Remove this endpoint in production.
    """
    try:
        # Validate required fields
        index_url = request.get("index_url")
        if not index_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="index_url is required"
            )
        
        index_type = request.get("index_type", "sheets")
        if index_type != "sheets":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only 'sheets' type is supported"
            )
        
        project_id = request.get("project_id", "project-chr-martech")
        client_id = request.get("client_id", "client-transparent-partners")
        
        # Extract sheet ID from Google Sheets URL
        sheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', index_url)
        if not sheet_id_match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google Sheets URL"
            )
        
        sheet_id = sheet_id_match.group(1)
        
        # Extract GID if present
        gid_match = re.search(r'[#&]gid=(\d+)', index_url)
        gid = int(gid_match.group(1)) if gid_match else 0
        
        logger.info(f"TEST: Analyzing Google Sheets {sheet_id} for project {project_id}")
        
        # Check if service account is properly initialized
        if not google_drive_service.credentials:
            logger.error("TEST: Service account credentials not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Service account not properly initialized"
            )
        
        logger.info(f"TEST: Service account email: {google_drive_service.service_account_email}")
        
        # Parse Google Sheets using hybrid approach (OAuth first, then service account)
        hybrid_client = HybridSheetsClient(
            user_credentials=None,  # No user OAuth in test mode
            service_account_credentials=google_drive_service.credentials,
            service_account_email=google_drive_service.service_account_email
        )
        
        rows = []
        sheet_name = "Sheet1"
        auth_method = "unknown"
        
        try:
            logger.info(f"TEST: Attempting to parse Google Sheets {sheet_id} with hybrid client")
            rows, sheet_name, auth_method = await hybrid_client.parse_sheet(sheet_id, gid or 0)
            logger.info(
                f"TEST: Successfully parsed {len(rows)} rows from '{sheet_name}' "
                f"using {auth_method}"
            )
        except Exception as e:
            logger.error(f"TEST: Hybrid client failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)  # HybridSheetsClient provides helpful error messages
            )
        
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data found in the Google Sheet"
            )
        
        # Process rows and create documents
        saved_docs = []
        logger.info(f"TEST: Processing {len(rows)} rows from sheet")
        
        for i, row in enumerate(rows):
            try:
                logger.info(f"TEST: Processing row {i+1}: {row}")
                
                # Extract document information from row
                title = row.get("Deliverable", f"Document {i+1}")
                link = row.get("Link", "")
                sow_number = row.get("SOW #", "")
                deliverable = row.get("Deliverable", "")
                owner = row.get("Responsible party", "")
                deliverable_id = row.get("DeliverableID", "")
                notes = row.get("Notes", "")
                
                logger.info(f"TEST: Extracted - title: '{title}', link: '{link}', sow: '{sow_number}'")
                
                if not title and not link:
                    logger.warning(f"TEST: Skipping row {i+1}: No title or link")
                    continue
                
                # Create document metadata using correct schema
                doc_id = f"doc-sheet-{sheet_id[:8]}-{i+1:03d}"
                
                # Determine if it's a Google Drive URL that requires permission
                requires_permission = link and ('drive.google.com' in link or 'docs.google.com' in link)
                
                doc_metadata = DocumentMetadata(
                    id=doc_id,
                    title=title or f"Document {i+1}",
                    type="document",
                    size=0,
                    uri="",  # GCS URI - empty until uploaded
                    status=DocumentStatus.REQUEST_ACCESS.value if requires_permission else DocumentStatus.UPLOADED.value,
                    upload_date=datetime.now().isoformat() + "Z",
                    media_type=MediaType.DOCUMENT,
                    doc_type=DocType.DELIVERABLE,
                    source_uri=link,
                    created_by="test-user",
                    sow_number=sow_number,
                    deliverable=deliverable,
                    responsible_party=owner,
                    deliverable_id=deliverable_id,
                    link=link,
                    notes=notes,
                    web_view_link=link,
                    requires_permission=requires_permission,
                    from_sheet_index=True,
                    sheet_index_id=sheet_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    client_id=client_id,
                    project_id=project_id,
                    visibility="project"
                )
                
                # Save to Firestore
                logger.info(f"TEST: Saving document {doc_id} to Firestore")
                doc_ref = firestore_client.db.collection("documents").document(doc_id)
                doc_ref.set(doc_metadata.dict())
                
                saved_docs.append({
                    "id": doc_id,
                    "title": doc_metadata.title,
                    "sow_number": sow_number,
                    "deliverable": deliverable,
                    "deliverable_id": deliverable_id,
                    "link": link,
                    "owner": owner,
                    "notes": notes
                })
                
                logger.info(f"TEST: Successfully created document {doc_id}: {title}")
                
            except Exception as e:
                logger.error(f"TEST: Error processing row {i+1}: {e}")
                continue
        
        if not saved_docs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid documents could be created from the sheet data"
            )
        
        # Build success message based on auth method used
        auth_message = ""
        if auth_method == "user_oauth":
            auth_message = " ✅ Used your Google account (no sharing needed!)"
        elif auth_method == "service_account":
            auth_message = f" ℹ️ Used service account ({google_drive_service.service_account_email})"
        
        return {
            "success": True,
            "documents_created": len(saved_docs),
            "documents": saved_docs,
            "message": f"TEST: Successfully analyzed Google Sheets and created {len(saved_docs)} document entries for project {project_id}.{auth_message}",
            "sheet_id": sheet_id,
            "sheet_name": sheet_name,
            "project_id": project_id,
            "client_id": client_id,
            "auth_method": auth_method,
            "auth_info": {
                "method_used": auth_method,
                "service_account_email": google_drive_service.service_account_email,
                "user_oauth_available": False
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TEST: Error analyzing document index: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TEST: Failed to analyze document index: {str(e)}"
        )


@app.post("/admin/analyze-document-index")
async def analyze_document_index(
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Analyze a document index (Google Sheets) and create individual document entries for a project.
    Now supports multi-tenant: documents are automatically assigned to specified project.
    """
    try:
        index_url = request.get("index_url", "").strip()
        index_type = request.get("index_type", "sheets").strip().lower()  # Default to sheets
        project_id = request.get("project_id", "project-chr-martech").strip()  # Project to assign documents to
        client_id = request.get("client_id", "client-transparent-partners").strip()  # Client to assign documents to
        
        if not index_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="index_url is required"
            )
        
        if index_type != "sheets":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only 'sheets' index_type is currently supported"
            )
        
        # Process Google Sheets index
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
        
        # NEW: Try to get user OAuth access token from request (optional)
        # Frontend can pass this to enable seamless access to user's own sheets
        oauth_access_token = request.get("oauth_access_token")
        user_credentials = None
        if oauth_access_token:
            from packages.shared.clients.auth import get_user_oauth_credentials
            user_credentials = await get_user_oauth_credentials(oauth_access_token)
            if user_credentials:
                logger.info("User OAuth credentials available - will try user access first")
        
        # Parse Google Sheets using hybrid approach (OAuth first, then service account)
        from packages.shared.clients.sheets import HybridSheetsClient
        hybrid_client = HybridSheetsClient(
            user_credentials=user_credentials,
            service_account_credentials=google_drive_service.credentials,
            service_account_email=google_drive_service.service_account_email
        )
        
        rows = []
        sheet_name = "Sheet1"
        auth_method = "unknown"
        
        try:
            logger.info(f"Attempting to parse Google Sheets {sheet_id} with hybrid client")
            rows, sheet_name, auth_method = await hybrid_client.parse_sheet(sheet_id, gid or 0)
            logger.info(
                f"Successfully parsed {len(rows)} rows from '{sheet_name}' "
                f"using {auth_method}"
            )
        except Exception as e:
            logger.error(f"Hybrid client failed: {e}")
            logger.info("Attempting fallback to public CSV access...")
            
            # Fallback: Try public Google Sheets API access without authentication
            try:
                logger.info("Attempting fallback to public Google Sheets API access...")
                
                # For public sheets, we can access them without authentication
                # by using the public API endpoint
                from googleapiclient.discovery import build
                
                # Create a service without credentials for public access
                service = build('sheets', 'v4', developerKey=None)
                
                # Get sheet name from GID
                sheet_name = "Sheet1"  # Default
                if gid and gid > 0:
                    try:
                        spreadsheet = service.spreadsheets().get(
                            spreadsheetId=sheet_id
                        ).execute()
                        
                        for sheet in spreadsheet.get('sheets', []):
                            sheet_props = sheet.get('properties', {})
                            if sheet_props.get('sheetId') == gid:
                                sheet_name = sheet_props.get('title', f'Sheet{gid}')
                                break
                    except Exception as meta_error:
                        logger.warning(f"Could not get sheet metadata: {meta_error}")
                
                # Get sheet data
                result = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=sheet_name
                ).execute()
                
                values = result.get('values', [])
                if not values:
                    raise Exception("No data found in sheet")
                
                # Convert to list of dicts
                headers = values[0]
                rows = []
                for row_values in values[1:]:
                    row_dict = {}
                    for i, header in enumerate(headers):
                        row_dict[header] = row_values[i] if i < len(row_values) else ""
                    rows.append(row_dict)
                
                auth_method = "public_api"
                logger.info(f"Successfully parsed {len(rows)} rows using public API access")
                    
            except Exception as api_error:
                logger.error(f"Public API fallback also failed: {api_error}")
                
                # Final fallback: Try CSV export as last resort
                try:
                    logger.info("Attempting final fallback to CSV export...")
                    import requests
                    
                    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid or 0}"
                    response = requests.get(export_url, timeout=30)
                    
                    if response.status_code == 200:
                        content = response.text
                        if not content.startswith('<'):
                            import csv
                            import io
                            
                            csv_reader = csv.DictReader(io.StringIO(content))
                            rows = []
                            for row in csv_reader:
                                cleaned_row = {}
                                for key, value in row.items():
                                    cleaned_key = key.strip()
                                    cleaned_value = value.strip() if value else ""
                                    cleaned_row[cleaned_key] = cleaned_value
                                rows.append(cleaned_row)
                            
                            if rows:
                                sheet_name = "Sheet1"
                                auth_method = "csv_export"
                                logger.info(f"Successfully parsed {len(rows)} rows using CSV export fallback")
                            else:
                                raise Exception("No data rows found in CSV export")
                        else:
                            raise Exception("CSV export returned HTML")
                    else:
                        raise Exception(f"CSV export failed with status {response.status_code}")
                        
                except Exception as csv_error:
                    logger.error(f"CSV export fallback also failed: {csv_error}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Unable to access Google Sheets. Service account failed: {str(e)}. Public API failed: {str(api_error)}. CSV export failed: {str(csv_error)}"
                    )
        
        # If no rows found, return error
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not parse Google Sheets or sheet is empty"
            )
        
        # Map rows to documents
        documents_found = []
        for i, row in enumerate(rows):
            # Skip empty rows (rows with no meaningful data)
            # Support multiple title column formats, including 'Deliverable' as title
            title = (row.get('Title') or row.get('title') or row.get('Document Title') or 
                    row.get('Deliverable') or row.get('deliverable') or '').strip()
            source_uri = (row.get('Link') or row.get('link') or row.get('URL') or '').strip()
            
            # Skip if both title and source_uri are empty
            if not title and not source_uri:
                continue
                
            # Use generated title if no title provided
            if not title:
                title = f"Document {len(documents_found)+1} from Sheet"
            
            doc_type_str = (row.get('Type') or row.get('type') or row.get('Doc Type') or 'misc').strip().lower()
            
            # Validate doc_type
            if doc_type_str not in ['sow', 'timeline', 'deliverable', 'misc']:
                doc_type_str = 'misc'
            
            # Determine status based on whether it's a Google Drive URL
            requires_permission = source_uri and ('drive.google.com' in source_uri or 'docs.google.com' in source_uri)
            initial_status = DocumentStatus.REQUEST_ACCESS if requires_permission else DocumentStatus.UPLOADED
            
            # Extract drive file ID if applicable
            drive_file_id = None
            web_view_link = source_uri  # Default to source_uri
            if requires_permission:
                match = re.search(r'/d/([a-zA-Z0-9_-]+)', source_uri)
                if match:
                    drive_file_id = match.group(1)
                    # Construct proper Drive view link if we have the file ID
                    if 'document' in source_uri:
                        web_view_link = f"https://docs.google.com/document/d/{drive_file_id}/edit"
                    elif 'spreadsheets' in source_uri:
                        web_view_link = f"https://docs.google.com/spreadsheets/d/{drive_file_id}/edit"
                    elif 'presentation' in source_uri:
                        web_view_link = f"https://docs.google.com/presentation/d/{drive_file_id}/edit"
                    else:
                        web_view_link = f"https://drive.google.com/file/d/{drive_file_id}/view"
            
            # Create document metadata using correct schema
            doc_id = f"doc-sheet-{sheet_id[:8]}-{i+1:03d}"
            
            doc_metadata = DocumentMetadata(
                id=doc_id,
                title=title,
                type="document",
                size=0,
                uri="",  # GCS URI - empty until uploaded
                status=initial_status.value,
                upload_date=datetime.now().isoformat() + "Z",
                media_type=MediaType.DOCUMENT,
                doc_type=DocType(doc_type_str),
                source_uri=source_uri,
                created_by=user["user"],
                sow_number=(row.get('SOW #') or row.get('sow_number') or '').strip(),
                deliverable=(row.get('Deliverable') or row.get('deliverable') or '').strip(),
                responsible_party=(row.get('Responsible party') or row.get('Responsible Party') or row.get('responsible_party') or '').strip(),
                deliverable_id=(row.get('DeliverableID') or row.get('Deliverable ID') or row.get('deliverable_id') or '').strip(),
                link=source_uri,
                notes=(row.get('Notes') or row.get('notes') or '').strip(),
                web_view_link=web_view_link,
                requires_permission=requires_permission,
                drive_file_id=drive_file_id,
                sheet_name=sheet_name,
                sheet_gid=str(gid) if gid else None,
                from_sheet_index=True,
                sheet_index_id=sheet_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                client_id=client_id,
                project_id=project_id,
                visibility="project"
            )
            documents_found.append(doc_metadata)
        
        # Save to Firestore
        saved_docs = []
        for doc_metadata in documents_found:
            try:
                await firestore_client.save_document(doc_metadata)
                saved_docs.append({
                    "id": doc_metadata.id,
                    "title": doc_metadata.title,
                    "sow_number": doc_metadata.sow_number,
                    "deliverable": doc_metadata.deliverable,
                    "deliverable_id": doc_metadata.deliverable_id,
                    "link": doc_metadata.link,
                    "owner": doc_metadata.responsible_party,
                    "notes": doc_metadata.notes
                })
            except Exception as e:
                logger.error(f"Error saving document {doc_metadata.id}: {e}")
                continue
        
        # Update project document count
        try:
            project_ref = firestore_client.db.collection("projects").document(project_id)
            project_ref.update({
                "document_count": firestore.Increment(len(saved_docs)),
                "updated_at": datetime.now()
            })
        except Exception as e:
            logger.warning(f"Could not update project document count: {e}")
        
        # Build success message based on auth method used
        auth_message = ""
        if auth_method == "user_oauth":
            auth_message = " ✅ Used your Google account (no sharing needed!)"
        elif auth_method == "service_account":
            auth_message = f" ℹ️ Used service account ({google_drive_service.service_account_email})"
        
        return {
            "success": True,
            "documents_created": len(saved_docs),
            "documents": saved_docs,
            "message": f"Successfully analyzed Google Sheets and created {len(saved_docs)} document entries for project {project_id}.{auth_message}",
            "sheet_id": sheet_id,
            "sheet_name": sheet_name,
            "project_id": project_id,
            "client_id": client_id,
            "auth_method": auth_method,
            "auth_info": {
                "method_used": auth_method,
                "service_account_email": google_drive_service.service_account_email,
                "user_oauth_available": user_credentials is not None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document index: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze document index: {str(e)}"
        )

@app.post("/admin/documents/{doc_id}/request-owner-access")
async def request_owner_access(
    doc_id: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Create an access request for document owner approval.
    Used when a document from the index needs owner permission.
    """
    try:
        # Get document from Firestore
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_snapshot = doc_ref.get()
        
        if not doc_snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        doc_data = doc_snapshot.to_dict()
        
        # Check if document requires permission
        if doc_data.get("status") != DocumentStatus.REQUEST_ACCESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document {doc_id} is not in 'request_access' status"
            )
        
        # Get owner email from document metadata
        owner_email = doc_data.get("responsible_party") or doc_data.get("owner")
        if not owner_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document does not have an owner email specified"
            )
        
        # Create access request
        access_request_id = f"access-req-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{doc_id[:8]}"
        access_request = DocumentAccessRequest(
            id=access_request_id,
            doc_id=doc_id,
            doc_title=doc_data.get("title", "Untitled Document"),
            doc_url=doc_data.get("source_uri", ""),
            owner_email=owner_email,
            requester_email=user["user"],
            project_id=doc_data.get("project_id", ""),
            client_id=doc_data.get("client_id", ""),
            status=AccessRequestStatus.PENDING,
            requested_at=datetime.now().isoformat() + "Z",
            bulk_request_id=doc_data.get("bulk_request_id")
        )
        
        # Save access request to Firestore
        access_req_ref = firestore_client.db.collection("access_requests").document(access_request_id)
        access_req_ref.set(access_request.dict())
        
        # Update document status to ACCESS_REQUESTED
        doc_ref.update({
            "status": DocumentStatus.ACCESS_REQUESTED.value,
            "access_requested": True,
            "access_requested_at": datetime.now(),
            "access_request_id": access_request_id,
            "updated_at": datetime.now()
        })
        
        logger.info(f"Created access request {access_request_id} for document {doc_id} from {owner_email}")
        
        return {
            "success": True,
            "access_request_id": access_request_id,
            "doc_id": doc_id,
            "owner_email": owner_email,
            "status": "access_requested",
            "message": f"Access request sent to document owner: {owner_email}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating access request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create access request: {str(e)}"
        )

@app.post("/admin/documents/bulk-request-owner-access")
async def bulk_request_owner_access(
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Create access requests for multiple documents from an index.
    Groups requests by owner for efficient notification.
    """
    try:
        doc_ids = request.get("doc_ids", [])
        index_url = request.get("index_url", "")
        index_title = request.get("index_title", "Document Index")
        project_id = request.get("project_id", "")
        client_id = request.get("client_id", "")
        
        if not doc_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="doc_ids array is required"
            )
        
        # Create bulk request record
        bulk_request_id = f"bulk-req-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        bulk_request = BulkAccessRequest(
            id=bulk_request_id,
            index_url=index_url,
            index_title=index_title,
            requester_email=user["user"],
            project_id=project_id,
            client_id=client_id,
            total_documents=len(doc_ids),
            pending_count=len(doc_ids),
            requested_at=datetime.now().isoformat() + "Z"
        )
        
        # Save bulk request
        bulk_req_ref = firestore_client.db.collection("bulk_access_requests").document(bulk_request_id)
        bulk_req_ref.set(bulk_request.dict())
        
        # Create individual access requests
        created_requests = []
        owner_groups = {}  # Group by owner for notification
        
        for doc_id in doc_ids:
            try:
                # Get document
                doc_ref = firestore_client.db.collection("documents").document(doc_id)
                doc_snapshot = doc_ref.get()
                
                if not doc_snapshot.exists:
                    logger.warning(f"Document {doc_id} not found, skipping")
                    continue
                
                doc_data = doc_snapshot.to_dict()
                
                # Get owner email
                owner_email = doc_data.get("responsible_party") or doc_data.get("owner")
                if not owner_email:
                    logger.warning(f"Document {doc_id} has no owner, skipping")
                    continue
                
                # Create access request
                access_request_id = f"access-req-{datetime.now().strftime('%Y%m%d%H%M%S')}-{doc_id[:8]}"
                access_request = DocumentAccessRequest(
                    id=access_request_id,
                    doc_id=doc_id,
                    doc_title=doc_data.get("title", "Untitled Document"),
                    doc_url=doc_data.get("source_uri", ""),
                    owner_email=owner_email,
                    requester_email=user["user"],
                    project_id=project_id,
                    client_id=client_id,
                    status=AccessRequestStatus.PENDING,
                    requested_at=datetime.now().isoformat() + "Z",
                    bulk_request_id=bulk_request_id
                )
                
                # Save access request
                access_req_ref = firestore_client.db.collection("access_requests").document(access_request_id)
                access_req_ref.set(access_request.dict())
                
                # Update document status
                doc_ref.update({
                    "status": DocumentStatus.ACCESS_REQUESTED.value,
                    "access_requested": True,
                    "access_requested_at": datetime.now(),
                    "access_request_id": access_request_id,
                    "bulk_request_id": bulk_request_id,
                    "updated_at": datetime.now()
                })
                
                created_requests.append(access_request_id)
                
                # Group by owner for notification
                if owner_email not in owner_groups:
                    owner_groups[owner_email] = []
                owner_groups[owner_email].append(access_request.dict())
                
            except Exception as e:
                logger.error(f"Error creating access request for {doc_id}: {e}")
                continue
        
        logger.info(f"Created {len(created_requests)} access requests across {len(owner_groups)} owners")
        
        return {
            "success": True,
            "bulk_request_id": bulk_request_id,
            "requests_created": len(created_requests),
            "owners_notified": len(owner_groups),
            "owner_groups": {owner: len(reqs) for owner, reqs in owner_groups.items()},
            "message": f"Created {len(created_requests)} access requests for {len(owner_groups)} document owners"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk access request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk access request failed: {str(e)}"
        )

@app.get("/admin/access-requests/pending")
async def get_pending_access_requests(
    owner_email: Optional[str] = None,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get pending access requests.
    If owner_email is provided, returns requests for that owner.
    Otherwise returns all pending requests (admin view).
    """
    try:
        query = firestore_client.db.collection("access_requests")
        query = query.where("status", "==", AccessRequestStatus.PENDING.value)
        
        # Filter by owner if specified
        if owner_email:
            query = query.where("owner_email", "==", owner_email)
        
        docs = query.stream()
        
        pending_requests = []
        for doc in docs:
            request_data = doc.to_dict()
            request_data["id"] = doc.id
            pending_requests.append(request_data)
        
        logger.info(f"Found {len(pending_requests)} pending access requests" + 
                   (f" for {owner_email}" if owner_email else ""))
        
        return {
            "requests": pending_requests,
            "total": len(pending_requests),
            "owner_email": owner_email
        }
        
    except Exception as e:
        logger.error(f"Error getting pending access requests: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending access requests: {str(e)}"
        )

@app.post("/admin/access-requests/{request_id}/approve")
async def approve_access_request(
    request_id: str,
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Approve an access request (called by document owner or admin).
    Updates document status to ACCESS_GRANTED.
    If share_with_team is enabled, downloads file to GCS for team access.
    """
    try:
        notes = request.get("notes", "")
        share_with_team = request.get("share_with_team", True)  # Default to enabling team access
        
        # Get access request
        access_req_ref = firestore_client.db.collection("access_requests").document(request_id)
        access_req_snapshot = access_req_ref.get()
        
        if not access_req_snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Access request {request_id} not found"
            )
        
        access_req_data = access_req_snapshot.to_dict()
        
        # Verify user is owner or admin
        if user["user"] != access_req_data["owner_email"] and "admin" not in user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the document owner or admin can approve this request"
            )
        
        # Update access request status
        access_req_ref.update({
            "status": AccessRequestStatus.APPROVED.value,
            "resolved_at": datetime.now().isoformat() + "Z",
            "resolution_notes": notes,
            "share_with_team": share_with_team,
            "team_access_granted": share_with_team
        })
        
        # Get document for processing
        doc_id = access_req_data["doc_id"]
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_snapshot = doc_ref.get()
        doc_data = doc_snapshot.to_dict() if doc_snapshot.exists else {}
        
        # Prepare document update
        doc_update = {
            "status": DocumentStatus.ACCESS_GRANTED.value,
            "access_granted": True,
            "access_granted_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Handle team access - download file to GCS if enabled
        gcs_copy_uri = None
        if share_with_team:
            try:
                drive_file_id = doc_data.get("drive_file_id")
                source_uri = doc_data.get("source_uri", "")
                
                if drive_file_id and google_drive_service.drive_service:
                    logger.info(f"Downloading Google Drive file {drive_file_id} for team access")
                    
                    # Download file from Google Drive using service account
                    from googleapiclient.http import MediaIoBaseDownload
                    import io
                    from google.cloud import storage
                    
                    # Get file metadata
                    file_metadata = google_drive_service.drive_service.files().get(
                        fileId=drive_file_id,
                        fields="name,mimeType,size"
                    ).execute()
                    
                    file_name = file_metadata.get("name", f"document_{doc_id}")
                    mime_type = file_metadata.get("mimeType", "application/octet-stream")
                    
                    # Download file content
                    request_dl = google_drive_service.drive_service.files().get_media(fileId=drive_file_id)
                    file_buffer = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_buffer, request_dl)
                    
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            logger.info(f"Download progress: {int(status.progress() * 100)}%")
                    
                    # Upload to GCS
                    project_id = os.getenv("GCP_PROJECT", "transparent-agent-test")
                    bucket_name = f"{project_id}-documents"
                    
                    storage_client = storage.Client(project=project_id)
                    bucket = storage_client.bucket(bucket_name)
                    
                    # Create blob path: project/client/doc_id/filename
                    blob_path = f"{access_req_data['project_id']}/{access_req_data['client_id']}/{doc_id}/{file_name}"
                    blob = bucket.blob(blob_path)
                    
                    # Upload with metadata
                    file_buffer.seek(0)
                    blob.upload_from_file(
                        file_buffer,
                        content_type=mime_type,
                        timeout=300
                    )
                    
                    # Set read-only access for project team (using IAM conditions in production)
                    # For now, just make it accessible via signed URLs
                    gcs_copy_uri = f"gs://{bucket_name}/{blob_path}"
                    
                    logger.info(f"Successfully uploaded file to {gcs_copy_uri}")
                    
                    # Update document with GCS info
                    doc_update.update({
                        "team_can_download": True,
                        "team_access_permission": "download",
                        "gcs_copy_uri": gcs_copy_uri,
                        "original_file_downloaded": True
                    })
                else:
                    logger.warning(f"No drive_file_id found for document {doc_id}, skipping team access setup")
                    doc_update.update({
                        "team_can_download": False,
                        "team_access_permission": "view"
                    })
                    
            except Exception as e:
                logger.error(f"Error downloading file for team access: {e}", exc_info=True)
                # Don't fail the approval, just log the error
                doc_update.update({
                    "team_can_download": False,
                    "team_access_permission": "view",
                    "team_access_error": str(e)
                })
        else:
            # No team access - AI chat only
            doc_update.update({
                "team_can_download": False,
                "team_access_permission": "none"
            })
        
        # Update document
        doc_ref.update(doc_update)
        
        # Update bulk request counts if applicable
        bulk_request_id = access_req_data.get("bulk_request_id")
        if bulk_request_id:
            bulk_req_ref = firestore_client.db.collection("bulk_access_requests").document(bulk_request_id)
            bulk_req_ref.update({
                "approved_count": firestore.Increment(1),
                "pending_count": firestore.Increment(-1)
            })
        
        team_access_msg = ""
        if share_with_team and gcs_copy_uri:
            team_access_msg = " Team can now view and download (read-only)."
        elif share_with_team:
            team_access_msg = " Team access enabled (view only - download failed)."
        else:
            team_access_msg = " AI chat only (no team downloads)."
        
        logger.info(f"Access request {request_id} approved by {user['user']} for document {doc_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "doc_id": doc_id,
            "status": "approved",
            "share_with_team": share_with_team,
            "team_can_download": doc_update.get("team_can_download", False),
            "gcs_copy_uri": gcs_copy_uri,
            "message": f"Access request approved. Document {doc_id} is now accessible.{team_access_msg}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving access request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve access request: {str(e)}"
        )

@app.post("/admin/access-requests/{request_id}/deny")
async def deny_access_request(
    request_id: str,
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Deny an access request (called by document owner or admin).
    Updates document status to QUARANTINED.
    """
    try:
        notes = request.get("notes", "Access denied by document owner")
        
        # Get access request
        access_req_ref = firestore_client.db.collection("access_requests").document(request_id)
        access_req_snapshot = access_req_ref.get()
        
        if not access_req_snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Access request {request_id} not found"
            )
        
        access_req_data = access_req_snapshot.to_dict()
        
        # Verify user is owner or admin
        if user["user"] != access_req_data["owner_email"] and "admin" not in user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the document owner or admin can deny this request"
            )
        
        # Update access request status
        access_req_ref.update({
            "status": AccessRequestStatus.DENIED.value,
            "resolved_at": datetime.now().isoformat() + "Z",
            "resolution_notes": notes
        })
        
        # Update document status to quarantined
        doc_id = access_req_data["doc_id"]
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_ref.update({
            "status": DocumentStatus.QUARANTINED.value,
            "access_granted": False,
            "updated_at": datetime.now()
        })
        
        # Update bulk request counts if applicable
        bulk_request_id = access_req_data.get("bulk_request_id")
        if bulk_request_id:
            bulk_req_ref = firestore_client.db.collection("bulk_access_requests").document(bulk_request_id)
            bulk_req_ref.update({
                "denied_count": firestore.Increment(1),
                "pending_count": firestore.Increment(-1)
            })
        
        logger.info(f"Access request {request_id} denied by {user['user']} for document {doc_id}")
        
        return {
            "success": True,
            "request_id": request_id,
            "doc_id": doc_id,
            "status": "denied",
            "message": f"Access request denied. Document {doc_id} has been quarantined."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error denying access request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deny access request: {str(e)}"
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
                    valid_categories = [dt.value for dt in DocType]
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
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Assign a document to a specific category using enhanced classification system.
    """
    try:
        doc_type = request.get("doc_type", "").strip()
        category = request.get("category", "").strip()
        subcategory = request.get("subcategory", "").strip()
        
        if not doc_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="doc_type is required"
            )
        
        # Validate doc_type
        valid_doc_types = [dt.value for dt in DocType]
        if doc_type not in valid_doc_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid doc_type. Must be one of: {valid_doc_types}"
            )
        
        # Validate category if provided
        if category:
            valid_categories = [cat.value for cat in DocumentCategory]
            if category not in valid_categories:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category. Must be one of: {valid_categories}"
                )
        
        # Validate subcategory if provided
        if subcategory:
            valid_subcategories = [sub.value for sub in DocumentSubcategory]
            if subcategory not in valid_subcategories:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid subcategory. Must be one of: {valid_subcategories}"
                )
        
        # Find and update document in Firestore
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_snapshot = doc_ref.get()
        
        if not doc_snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        # Update the document with new classification
        doc_data = doc_snapshot.to_dict()
        
        # Update legacy doc_type field
        doc_data["doc_type"] = doc_type
        doc_data["updated_at"] = datetime.now()
        
        # Update enhanced classification if provided
        if category or subcategory:
            # Get or create classification info
            if "classification" not in doc_data:
                doc_data["classification"] = {}
            
            doc_data["classification"]["doc_type"] = doc_type
            if category:
                doc_data["classification"]["category"] = category
            if subcategory:
                doc_data["classification"]["subcategory"] = subcategory
            
            # Mark as manually reviewed
            doc_data["classification_reviewed"] = True
            doc_data["classification_reviewed_by"] = user.get("user", "admin")
            doc_data["classification_reviewed_at"] = datetime.now()
            doc_data["auto_classified"] = False
        
        # Save updated document to Firestore
        doc_ref.set(doc_data)
        
        return {
            "success": True,
            "doc_id": doc_id,
            "doc_type": doc_type,
            "category": category,
            "subcategory": subcategory,
            "message": f"Document assigned to {doc_type} type"
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
        # Validate category - now supports all DocType values
        valid_categories = [dt.value for dt in DocType]
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
    Get all documents pending approval from Firestore.
    """
    try:
        docs_ref = firestore_client.db.collection("documents")
        
        # Query for all pending statuses
        pending_statuses = [
            DocumentStatus.UPLOADED.value,
            DocumentStatus.REQUEST_ACCESS.value,
            DocumentStatus.ACCESS_REQUESTED.value,
            DocumentStatus.ACCESS_GRANTED.value,
            DocumentStatus.AWAITING_PROCESSING.value
        ]
        
        all_pending_docs = []
        for status_value in pending_statuses:
            query = docs_ref.where("status", "==", status_value)
            docs = query.stream()
            
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["id"] = doc.id
                all_pending_docs.append(doc_data)
        
        logger.info(f"Found {len(all_pending_docs)} pending documents in Firestore")
        
        return {
            "documents": all_pending_docs,
            "total": len(all_pending_docs)
        }
        
    except Exception as e:
        logger.error(f"Error getting pending documents: {e}", exc_info=True)
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
        # Get document from Firestore
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_snapshot = doc_ref.get()
        
        if not doc_snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        doc_data = doc_snapshot.to_dict()
        current_status = doc_data.get("status")
        
        # Check if document is in a state that can be approved
        if current_status not in [DocumentStatus.UPLOADED.value, DocumentStatus.ACCESS_GRANTED.value, DocumentStatus.AWAITING_APPROVAL.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document {doc_id} with status '{current_status}' cannot be approved. Must be 'uploaded', 'access_granted', or 'awaiting_approval'"
            )
        
        # Prepare update data - move to "approved" status (document approved, visible in library)
        update_data = {
            "status": DocumentStatus.APPROVED.value,
            "approved_by": user["user"],
            "approved_date": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now()
        }
        
        # If doc_type is provided, update it
        if "doc_type" in request:
            valid_categories = [dt.value for dt in DocType]
            if request["doc_type"] in valid_categories:
                update_data["doc_type"] = request["doc_type"]
        
        # Update document in Firestore
        doc_ref.update(update_data)
        
        # Log the approval
        logger.info(f"Document {doc_id} approved by {user['user']} with status {update_data['status']}")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "status": update_data["status"],
            "doc_type": update_data.get("doc_type", doc_data.get("doc_type")),
            "message": f"Document {doc_id} approved! Document is now available in the {update_data.get('doc_type', 'misc')} section. Submit for AI processing to enable chat functionality."
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
    Delete a single document from Firestore.
    """
    try:
        # Get document from Firestore first
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        doc_to_delete = doc.to_dict()
        
        # Delete from Firestore
        doc_ref.delete()
        logger.info(f"Deleted document {doc_id} from Firestore")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "deleted_document": doc_to_delete,
            "message": f"Document {doc_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@app.post("/admin/documents/bulk-delete")
async def bulk_delete_documents(
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Bulk delete documents. Useful for clearing inventory before importing new template.
    
    Request body:
    {
        "doc_ids": ["doc1", "doc2", ...],  // List of specific doc IDs
        "delete_all": false,  // Set to true to delete ALL documents (use with caution!)
        "project_id": "project-xxx",  // Optional: Delete only documents in this project
        "client_id": "client-xxx"  // Optional: Delete only documents in this client
    }
    """
    try:
        doc_ids = request.get("doc_ids", [])
        delete_all = request.get("delete_all", False)
        project_id = request.get("project_id")
        client_id = request.get("client_id")
        
        deleted_count = 0
        failed_count = 0
        deleted_docs = []
        
        # Option 1: Delete specific documents by ID
        if doc_ids:
            for doc_id in doc_ids:
                try:
                    doc_ref = firestore_client.db.collection("documents").document(doc_id)
                    doc = doc_ref.get()
                    if doc.exists:
                        doc_ref.delete()
                        deleted_docs.append(doc_id)
                        deleted_count += 1
                        logger.info(f"Deleted document {doc_id}")
                    else:
                        failed_count += 1
                        logger.warning(f"Document {doc_id} not found")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to delete {doc_id}: {str(e)}")
        
        # Option 2: Delete all documents (with optional filtering)
        elif delete_all:
            query = firestore_client.db.collection("documents")
            
            # Apply filters if provided
            if project_id:
                query = query.where("project_id", "==", project_id)
            if client_id:
                query = query.where("client_id", "==", client_id)
            
            # Get all matching documents
            docs = query.stream()
            
            for doc in docs:
                try:
                    doc.reference.delete()
                    deleted_docs.append(doc.id)
                    deleted_count += 1
                    logger.info(f"Deleted document {doc.id}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to delete {doc.id}: {str(e)}")
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'doc_ids' array or 'delete_all: true' must be provided"
            )
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "deleted_docs": deleted_docs,
            "message": f"Successfully deleted {deleted_count} documents" + 
                      (f", {failed_count} failed" if failed_count > 0 else "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk delete failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk delete failed: {str(e)}"
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
        # Validate category - now supports all DocType values
        valid_categories = [dt.value for dt in DocType]
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
        # Validate category - now supports all DocType values
        valid_categories = [dt.value for dt in DocType]
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

@app.post("/admin/documents/{doc_id}/submit-processing")
async def submit_for_processing(
    doc_id: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Submit a document for AI processing.
    Moves from 'access_granted' to 'awaiting_processing' status.
    """
    try:
        # Get document from Firestore
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_snapshot = doc_ref.get()
        
        if not doc_snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        doc_data = doc_snapshot.to_dict()
        current_status = doc_data.get("status")
        
        # Check if document is in approved status
        if current_status != DocumentStatus.APPROVED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document {doc_id} with status '{current_status}' cannot be submitted for processing. Must be 'approved'"
            )
        
        # Update document to processing_requested status
        update_data = {
            "status": DocumentStatus.PROCESSING_REQUESTED.value,
            "processing_requested_by": user["user"],
            "processing_requested_date": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now()
        }
        
        doc_ref.update(update_data)
        
        # Log the processing request
        logger.info(f"Document {doc_id} submitted for processing by {user['user']}")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "status": update_data["status"],
            "doc_type": doc_data.get("doc_type", "misc"),
            "message": f"Document {doc_id} submitted for AI processing. Document remains available in {doc_data.get('doc_type', 'misc')} section."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit document for processing: {str(e)}"
        )

@app.post("/admin/documents/{doc_id}/process")
async def process_document(
    doc_id: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Process a document that has been approved and is awaiting processing.
    This moves it from 'awaiting_processing' to 'document_processed' status.
    """
    try:
        # Get document from Firestore
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_snapshot = doc_ref.get()
        
        if not doc_snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        doc_data = doc_snapshot.to_dict()
        current_status = doc_data.get("status")
        
        # Check if document is in processing_requested status
        if current_status != DocumentStatus.PROCESSING_REQUESTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document {doc_id} with status '{current_status}' cannot be processed. Must be 'processing_requested'"
            )
        
        # Update document to processing status (then to processed)
        update_data = {
            "status": DocumentStatus.PROCESSING.value,
            "processing_started_by": user["user"],
            "processing_started_date": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now()
        }
        
        doc_ref.update(update_data)
        
        # Simulate processing time and move to processed
        # In real implementation, this would be handled by a background worker
        final_update = {
            "status": DocumentStatus.PROCESSED.value,
            "processed_by": user["user"],
            "processed_date": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now()
        }
        
        # Log the processing
        logger.info(f"Document {doc_id} processed by {user['user']} - now available for AI chat in {doc_data.get('doc_type', 'misc')} section")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "status": final_update["status"],
            "doc_type": doc_data.get("doc_type", "misc"),
            "message": f"Document {doc_id} processed successfully! Document is now available for AI chat in the {doc_data.get('doc_type', 'misc')} section."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

@app.get("/inventory", response_model=InventoryResponse)
async def get_inventory(
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    doc_type: Optional[str] = None,
    media_type: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    created_by: Optional[str] = None,
    topics: Optional[str] = None,
    client_id: Optional[str] = None,  # NEW: Filter by client
    project_id: Optional[str] = None,  # NEW: Filter by project
    user: dict = Depends(require_admin_auth)
) -> InventoryResponse:
    """
    Get document inventory with filtering and pagination.
    Now supports multi-tenant filtering by client_id and project_id.
    """
    try:
        # Parse topics if provided
        topic_list = topics.split(",") if topics else None
        
        # Query Firestore for documents
        docs_ref = firestore_client.db.collection("documents")
        
        # Apply RBAC filters (NEW)
        if project_id:
            docs_ref = docs_ref.where("project_id", "==", project_id)
        elif client_id:
            docs_ref = docs_ref.where("client_id", "==", client_id)
        
        # Apply other filters
        if doc_type:
            docs_ref = docs_ref.where("doc_type", "==", doc_type)
        if media_type:
            docs_ref = docs_ref.where("media_type", "==", media_type)
        if status:
            docs_ref = docs_ref.where("status", "==", status)
        if created_by:
            docs_ref = docs_ref.where("created_by", "==", created_by)
        
        # Get all matching documents
        docs = docs_ref.stream()
        
        # Convert to list and apply text search
        all_docs = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data["id"] = doc.id
            
            # Apply text search if provided
            if q:
                searchable_text = f"{doc_data.get('title', '')} {doc_data.get('notes', '')}".lower()
                if q.lower() not in searchable_text:
                    continue
            
            # Apply topic filter if provided
            if topic_list:
                doc_topics = doc_data.get('topics', [])
                if not any(topic.lower() in [t.lower() for t in doc_topics] for topic in topic_list):
                    continue
            
            all_docs.append(doc_data)
        
        # Sort documents with robust handling of different types
        reverse = sort_order == "desc"
        
        def safe_sort_key(doc):
            """Safe sort key that handles different data types."""
            value = doc.get(sort_by)
            
            # Handle datetime objects
            if isinstance(value, datetime):
                return value.isoformat()
            
            # Handle None or empty
            if value is None or value == "":
                return "0000-00-00" if sort_by == "created_at" else ""
            
            # Convert to string for consistent sorting
            return str(value)
        
        try:
            all_docs.sort(key=safe_sort_key, reverse=reverse)
        except Exception as e:
            logger.warning(f"Sort failed, using default order: {e}")
            # Fallback: sort by document ID if sort fails
            all_docs.sort(key=lambda x: x.get("id", ""), reverse=True)
        
        # Apply pagination
        total = len(all_docs)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total)  # Ensure we don't exceed total
        paginated_docs = all_docs[start_idx:end_idx]
        
        logger.info(f"Pagination: page={page}, total={total}, start={start_idx}, end={end_idx}, items={len(paginated_docs)}")
        
        # Convert to inventory items with error handling
        items = []
        for doc in paginated_docs:
            try:
                # Ensure created_at is in proper format
                created_at_value = doc.get("created_at")
                if isinstance(created_at_value, datetime):
                    created_at_str = created_at_value.isoformat()
                elif created_at_value:
                    created_at_str = str(created_at_value)
                else:
                    created_at_str = datetime.now().isoformat()
                
                item = InventoryItem(
                    doc_id=doc.get("id", "unknown"),
                    title=doc.get("title", "Untitled"),
                    doc_type=doc.get("doc_type", "misc"),
                    media_type=doc.get("media_type", "document"),
                    status=doc.get("status", "uploaded"),
                    created_by=doc.get("created_by", "unknown"),
                    created_at=created_at_str,
                    topics=doc.get("topics", []) if isinstance(doc.get("topics"), list) else [],
                    thumbnail=doc.get("thumbnails", {}).get("small") if isinstance(doc.get("thumbnails"), dict) else None
                )
                items.append(item)
            except Exception as e:
                logger.error(f"Error converting document {doc.get('id', 'unknown')} to InventoryItem: {e}")
                # Skip this document but continue processing others
                continue
        
        total_pages = (total + page_size - 1) // page_size
        
        return InventoryResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error getting inventory: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inventory: {str(e)}"
        )

@app.post("/admin/migrate-to-rbac")
async def migrate_to_rbac(
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Migrate all existing documents to default client and project.
    This is a one-time migration endpoint.
    """
    try:
        client_id = request.get("client_id", "client-transparent-partners")
        project_id = request.get("project_id", "project-chr-martech")
        
        # Get all documents without client_id or project_id
        docs_ref = firestore_client.db.collection("documents")
        all_docs = docs_ref.stream()
        
        migrated = 0
        skipped = 0
        
        for doc in all_docs:
            doc_data = doc.to_dict()
            
            # Skip if already has tenant fields
            if doc_data.get("client_id") and doc_data.get("project_id"):
                skipped += 1
                continue
            
            # Add tenant fields
            doc.reference.update({
                "client_id": client_id,
                "project_id": project_id,
                "visibility": "project",
                "updated_at": datetime.now()
            })
            
            migrated += 1
        
        # Update project document count
        project_ref = firestore_client.db.collection("projects").document(project_id)
        project_ref.update({
            "document_count": migrated,
            "updated_at": datetime.now()
        })
        
        logger.info(f"RBAC Migration: {migrated} documents migrated, {skipped} skipped")
        
        return {
            "success": True,
            "migrated": migrated,
            "skipped": skipped,
            "client_id": client_id,
            "project_id": project_id,
            "message": f"Successfully migrated {migrated} documents to {project_id}"
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )

@app.get("/documents/{doc_id}/download-url")
async def get_document_download_url(
    doc_id: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get download URL for a document (project team members only).
    Returns signed URL for GCS file and link to original for editing.
    
    Permission model:
    - Transparent users (@transparent.partners): Can edit in Google Drive
    - Client users (external): Can download only (no edit)
    """
    try:
        # Get document from Firestore
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_snapshot = doc_ref.get()
        
        if not doc_snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        doc_data = doc_snapshot.to_dict()
        
        # Check user has access to this document's project
        doc_project_id = doc_data.get("project_id")
        # TODO: In production, check user's project access from JWT
        # For now, all authenticated @transparent.partners users have access
        
        # Determine user type
        user_email = user.get("user", "")
        is_transparent_user = user_email.endswith("@transparent.partners")
        
        # Check if document has team download enabled
        team_can_download = doc_data.get("team_can_download", False)
        gcs_copy_uri = doc_data.get("gcs_copy_uri")
        source_uri = doc_data.get("source_uri", "")
        web_view_link = doc_data.get("web_view_link", source_uri)
        
        response = {
            "doc_id": doc_id,
            "title": doc_data.get("title", "Untitled"),
            "user_type": "transparent" if is_transparent_user else "client",
            "can_download": team_can_download,
            "can_edit": is_transparent_user and bool(web_view_link),  # Only Transparent users can edit
            "edit_url": web_view_link if (is_transparent_user and web_view_link) else None,
            "download_url": None,
            "team_access_permission": doc_data.get("team_access_permission", "none"),
            "access_note": "Transparent users can edit in Google Drive. Client users can download only."
        }
        
        # Generate signed URL for download if available
        if team_can_download and gcs_copy_uri:
            try:
                from google.cloud import storage
                from datetime import timedelta
                
                # Parse GCS URI (gs://bucket/path/to/file)
                if gcs_copy_uri.startswith("gs://"):
                    parts = gcs_copy_uri[5:].split("/", 1)
                    bucket_name = parts[0]
                    blob_path = parts[1] if len(parts) > 1 else ""
                    
                    project_id = os.getenv("GCP_PROJECT", "transparent-agent-test")
                    storage_client = storage.Client(project=project_id)
                    bucket = storage_client.bucket(bucket_name)
                    blob = bucket.blob(blob_path)
                    
                    # Generate signed URL valid for 1 hour
                    signed_url = blob.generate_signed_url(
                        version="v4",
                        expiration=timedelta(hours=1),
                        method="GET"
                    )
                    
                    response["download_url"] = signed_url
                    logger.info(f"Generated download URL for document {doc_id} for user {user['user']} (type: {'transparent' if is_transparent_user else 'client'})")
                    
            except Exception as e:
                logger.error(f"Error generating signed URL: {e}", exc_info=True)
                response["download_error"] = "Failed to generate download link"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document access: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document access: {str(e)}"
        )

@app.get("/documents/{doc_id}/access-info")
async def get_document_access_info(
    doc_id: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get document access information for displaying in the UI.
    Shows what actions are available to the user based on their type.
    
    Transparent users: Can view, download, and edit
    Client users: Can view and download only
    """
    try:
        # Get document from Firestore
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_snapshot = doc_ref.get()
        
        if not doc_snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        doc_data = doc_snapshot.to_dict()
        
        # Determine user type
        user_email = user.get("user", "")
        is_transparent_user = user_email.endswith("@transparent.partners")
        
        # Build access info with user-type-specific permissions
        return {
            "doc_id": doc_id,
            "title": doc_data.get("title", "Untitled"),
            "status": doc_data.get("status"),
            "doc_type": doc_data.get("doc_type"),
            "user_type": "transparent" if is_transparent_user else "client",
            "access": {
                "can_view_metadata": True,  # All project members can view metadata
                "can_search_ai": doc_data.get("status") in ["processed", "approved"],  # AI search available to all
                "can_download": doc_data.get("team_can_download", False),  # Download available to all if enabled
                "can_edit": is_transparent_user and bool(doc_data.get("web_view_link")),  # Only Transparent users can edit
                "team_access_permission": doc_data.get("team_access_permission", "none"),
                "edit_permission_note": "Editing available to Transparent users only" if not is_transparent_user else None
            },
            "urls": {
                "edit_url": doc_data.get("web_view_link") if is_transparent_user else None,  # Only for Transparent users
                "source_url": doc_data.get("source_uri"),   # Original source
                "download_url_endpoint": f"/documents/{doc_id}/download-url"  # Call this to get signed URL
            },
            "metadata": {
                "owner": doc_data.get("owner") or doc_data.get("responsible_party"),
                "created_at": doc_data.get("created_at"),
                "updated_at": doc_data.get("updated_at"),
                "project_id": doc_data.get("project_id"),
                "client_id": doc_data.get("client_id")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document access info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document access info: {str(e)}"
        )

@app.post("/test-assign-category")
async def test_assign_document_category(
    doc_id: str,
    category: str
) -> Dict[str, Any]:
    """
    TEST ENDPOINT: Assign document to a specific category without authentication.
    """
    try:
        if not category or not category.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="category is required"
            )
        
        category = category.strip()
        
        # Validate category - now supports all DocType values
        valid_categories = [dt.value for dt in DocType]
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )
        
        # Find and update document in Firestore
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_snapshot = doc_ref.get()
        
        if not doc_snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        # Update the document with new category
        doc_data = doc_snapshot.to_dict()
        doc_data["doc_type"] = category
        doc_data["updated_at"] = datetime.now()
        
        # Save updated document to Firestore
        doc_ref.set(doc_data)
        
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

@app.get("/test-inventory", response_model=InventoryResponse)
async def test_get_inventory(
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    doc_type: Optional[str] = None,
    media_type: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    created_by: Optional[str] = None,
    topics: Optional[str] = None,
    client_id: Optional[str] = "client-transparent-partners",
    project_id: Optional[str] = "project-chr-martech"
) -> InventoryResponse:
    """
    TEST ENDPOINT: Get document inventory without authentication.
    This is for testing the inventory functionality.
    Remove this endpoint in production.
    """
    try:
        # Parse topics if provided
        topic_list = topics.split(",") if topics else None
        
        # Query Firestore for documents
        docs_ref = firestore_client.db.collection("documents")
        
        # Apply RBAC filters
        if project_id:
            docs_ref = docs_ref.where("project_id", "==", project_id)
        elif client_id:
            docs_ref = docs_ref.where("client_id", "==", client_id)
        
        # Apply other filters
        if doc_type:
            docs_ref = docs_ref.where("doc_type", "==", doc_type)
        if media_type:
            docs_ref = docs_ref.where("media_type", "==", media_type)
        if status:
            docs_ref = docs_ref.where("status", "==", status)
        if created_by:
            docs_ref = docs_ref.where("created_by", "==", created_by)
        
        # Get all matching documents
        docs = docs_ref.stream()
        
        # Convert to list and apply text search if needed
        documents = []
        for doc in docs:
            doc_data = doc.to_dict()
            
            # Apply text search if query provided
            if q:
                searchable_text = f"{doc_data.get('title', '')} {doc_data.get('sow_number', '')} {doc_data.get('deliverable', '')} {doc_data.get('responsible_party', '')}".lower()
                if q.lower() not in searchable_text:
                    continue
            
            # Apply topic filter if provided
            if topic_list:
                doc_topics = doc_data.get('topics', [])
                if not any(topic in doc_topics for topic in topic_list):
                    continue
            
            # Convert to InventoryItem
            created_at = doc_data.get('created_at')
            if created_at and hasattr(created_at, 'isoformat'):
                created_at_str = created_at.isoformat()
            else:
                created_at_str = str(created_at) if created_at else ''
            
            inventory_item = InventoryItem(
                doc_id=doc_data.get('id', doc.id),
                title=doc_data.get('title', ''),
                doc_type=DocType(doc_data.get('doc_type', 'document')),
                media_type=MediaType(doc_data.get('media_type', 'document')),
                status=DocumentStatus(doc_data.get('status', 'uploaded')),
                created_by=doc_data.get('created_by', ''),
                created_at=created_at_str,
                topics=doc_data.get('topics', [])
            )
            documents.append(inventory_item)
        
        # Sort documents
        reverse = sort_order.lower() == "desc"
        if sort_by == "created_at":
            documents.sort(key=lambda x: x.created_at or '', reverse=reverse)
        elif sort_by == "title":
            documents.sort(key=lambda x: x.title.lower(), reverse=reverse)
        elif sort_by == "doc_type":
            documents.sort(key=lambda x: x.doc_type.value.lower() if hasattr(x.doc_type, 'value') else str(x.doc_type).lower(), reverse=reverse)
        
        # Apply pagination
        total_docs = len(documents)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_docs = documents[start_idx:end_idx]
        
        return InventoryResponse(
            items=paginated_docs,
            total=total_docs,
            page=page,
            page_size=page_size,
            total_pages=(total_docs + page_size - 1) // page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting inventory: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inventory: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "admin-api", "rbac_enabled": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
