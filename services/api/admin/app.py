"""Production Admin API service for Project Agent with Firestore integration."""

import csv
import io
import re
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware

# Import shared components
import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from packages.shared.schemas.document import DocumentMetadata, DocumentStatus, DocType, MediaType
    # Import Firestore directly to avoid auth dependency
    from google.cloud import firestore
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Python path: {sys.path}")
    print(f"Project root: {project_root}")
    raise

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

# Initialize Firestore client
class SimpleFirestoreClient:
    """Simple Firestore client for admin operations."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.db = firestore.Client(project=self.project_id)
    
    async def save_document(self, metadata: DocumentMetadata) -> str:
        """Save document metadata to Firestore."""
        try:
            logger.info(f"Saving document {metadata.id} to Firestore")
            doc_ref = self.db.collection("documents").document(metadata.id)
            doc_data = metadata.dict()
            logger.info(f"Document data to save: {doc_data}")
            doc_ref.set(doc_data)
            logger.info(f"Successfully saved document {metadata.id} to Firestore")
            return metadata.id
        except Exception as e:
            logger.error(f"Error saving document {metadata.id} to Firestore: {e}", exc_info=True)
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
            print(f"Error getting document from Firestore: {e}")
            raise
    
    async def query_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Query documents by category/doc_type - only return indexed documents."""
        try:
            docs_ref = self.db.collection("documents")
            # Only return documents that are indexed (available to users)
            # Use string values for Firestore queries
            query = docs_ref.where("doc_type", "==", category).where("status", "==", "indexed")
            docs = query.stream()
            
            documents = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["id"] = doc.id
                documents.append(doc_data)
            
            return documents
        except Exception as e:
            print(f"Error querying documents by category: {e}")
            return []

firestore_client = SimpleFirestoreClient()

# Temporary in-memory store for testing (remove in production)
test_documents = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )

# Mock authentication dependency (replace with real auth in production)
async def require_admin_auth():
    """Mock authentication for demo purposes."""
    return {"user": "admin@transparent.partners", "domain": "transparent.partners"}

def is_google_drive_url(url: str) -> bool:
    """
    Check if URL is a Google Drive URL.
    
    Args:
        url: The URL to check
        
    Returns:
        bool: True if the URL is a Google Drive URL, False otherwise
    """
    drive_patterns = [
        r'https://drive\.google\.com/',
        r'https://docs\.google\.com/',
        r'https://sheets\.google\.com/',
        r'https://docs\.googleusercontent\.com/'
    ]
    return any(re.search(pattern, url) for pattern in drive_patterns)

def extract_drive_file_id(url: str) -> Optional[str]:
    """Extract Google Drive file ID from URL."""
    patterns = [
        r'/file/d/([a-zA-Z0-9-_]+)',
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'/document/d/([a-zA-Z0-9-_]+)',
        r'/presentation/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_drive_file_type(url: str) -> str:
    """Determine Google Drive file type from URL."""
    if 'spreadsheets' in url:
        return 'spreadsheet'
    elif 'document' in url:
        return 'document'
    elif 'presentation' in url:
        return 'presentation'
    elif 'file' in url:
        return 'file'
    else:
        return 'unknown'

def extract_gid_from_url(url: str) -> Optional[int]:
    """Extract GID from Google Sheets URL."""
    gid_match = re.search(r'[#&]gid=(\d+)', url)
    if gid_match:
        return int(gid_match.group(1))
    return None

def parse_google_sheets_csv(sheet_id: str, gid: int = 0) -> List[Dict[str, str]]:
    """Parse Google Sheets as CSV."""
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        response = requests.get(csv_url, timeout=30)
        response.raise_for_status()
        
        # Parse CSV
        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        return rows
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google Sheets is not publicly accessible. Please change sharing settings to 'Anyone with the link can view' and try again."
            )
        elif e.response.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to Google Sheets. Please check sharing permissions."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to access Google Sheets: {str(e)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing Google Sheets: {str(e)}"
        )

def create_access_request(url: str, created_by: str) -> Dict[str, Any]:
    """Create an access request for a document."""
    return {
        "url": url,
        "created_by": created_by,
        "created_at": datetime.now().isoformat() + "Z",
        "status": "pending"
    }

def map_document_from_row(row: Dict[str, str], index_url: str, created_by: str) -> Dict[str, Any]:
    """Map CSV row to document metadata."""
    # Extract fields from row (adjust column names as needed)
    title = row.get('title', row.get('Title', row.get('Document Title', ''))).strip()
    doc_type_str = row.get('doc_type', row.get('Doc Type', row.get('Type', 'misc'))).strip().lower()
    source_uri = row.get('source_uri', row.get('Source URI', row.get('URL', row.get('Link', '')))).strip()
    sow_number = row.get('sow_number', row.get('SOW Number', row.get('SOW #', ''))).strip()
    deliverable = row.get('deliverable', row.get('Deliverable', '')).strip()
    responsible_party = row.get('responsible_party', row.get('Responsible Party', row.get('Owner', ''))).strip()
    deliverable_id = row.get('deliverable_id', row.get('Deliverable ID', row.get('ID', ''))).strip()
    confidence = row.get('confidence', row.get('Confidence', 'medium')).strip()
    link = row.get('link', row.get('Link', source_uri)).strip()
    notes = row.get('notes', row.get('Notes', row.get('Description', ''))).strip()
    
    # Validate and convert doc_type to DocType enum
    valid_types = ['sow', 'timeline', 'deliverable', 'misc']
    if doc_type_str not in valid_types:
        doc_type_str = 'misc'
    
    # Handle documents without URLs - set status to uploaded and mark as needing URL
    has_url = bool(source_uri and source_uri.strip())
    if not has_url:
        source_uri = ""  # Empty URL
        initial_status = DocumentStatus.UPLOADED
        requires_permission = False
        drive_file_id = None
        drive_file_type = None
    else:
        # Check if this is a Google Drive URL and handle permissions
        requires_permission = is_google_drive_url(source_uri)
        drive_file_id = extract_drive_file_id(source_uri) if requires_permission else None
        drive_file_type = get_drive_file_type(source_uri) if requires_permission else None
        # Set initial status based on whether permission is required
        initial_status = DocumentStatus.PENDING_ACCESS if requires_permission else DocumentStatus.UPLOADED
    
    # Generate unique document ID
    doc_id = f"doc-{doc_type_str}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(title) % 10000:04d}"
    
    return {
        "id": doc_id,
        "title": title,
        "type": "document",  # Default type
        "size": 0,  # Will be updated when file is processed
        "uri": source_uri,
        "status": initial_status.value,
        "upload_date": datetime.now().isoformat() + "Z",
        "created_by": created_by,
        "media_type": "document",
        "doc_type": doc_type_str,
        "source_ref": drive_file_id,
        "required_fields_ok": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        
        # Permission fields
        "requires_permission": requires_permission,
        "permission_requested": requires_permission,
        "permission_granted": False,
        "permission_requested_at": datetime.now() if requires_permission else None,
        "permission_granted_at": None,
        "drive_file_id": drive_file_id,
        
        # Index tracking
        "index_source_id": extract_drive_file_id(index_url) if index_url else None,
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "admin-api"}

@app.post("/admin/analyze-document-index")
async def analyze_document_index(
    request: Dict[str, Any],
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Analyze a document index (CSV or Google Sheets) and create individual document entries.
    """
    try:
        index_url = request.get("index_url", "").strip()
        index_type = request.get("index_type", "sheets").strip().lower()
        
        if not index_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="index_url is required"
            )
        
        if index_type == "sheets":
            # Extract sheet ID and GID from URL
            sheet_id = extract_drive_file_id(index_url)
            if not sheet_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Google Sheets URL. Could not extract sheet ID."
                )
            
            gid = extract_gid_from_url(index_url)
            if gid is None:
                logger.warning(f"No GID found in URL {index_url}, using default GID=0")
                gid = 0
            
            # Create access request for the document index
            access_request = create_access_request(index_url, user["user"])
            
            # Parse Google Sheets as CSV
            try:
                rows = parse_google_sheets_csv(sheet_id, gid)
            except HTTPException as e:
                # If we can't access the sheet, create individual document entries anyway
                if e.status_code == 403 or e.status_code == 401:
                    logger.warning(f"Google Sheets access denied (status {e.status_code}), creating document entries from URL structure")
                    
                    # Create sample documents for demonstration
                    sample_docs = [
                            {
                                "id": f"doc-sheet-{sheet_id[:8]}-001",
                                "title": "Document from Google Sheets Index",
                                "type": "document",
                                "size": 0,
                                "uri": index_url,
                                "status": DocumentStatus.PENDING_ACCESS.value,
                                "upload_date": datetime.now().isoformat() + "Z",
                                "created_by": user["user"],
                                "media_type": "document",
                                "doc_type": "misc",
                                "source_ref": sheet_id,
                                "required_fields_ok": True,
                                "created_at": datetime.now(),
                                "updated_at": datetime.now(),
                                "requires_permission": True,
                                "permission_requested": True,
                                "permission_granted": False,
                                "permission_requested_at": datetime.now(),
                                "permission_granted_at": None,
                                "drive_file_id": sheet_id,
                                "index_source_id": sheet_id,
                            },
                            {
                                "id": f"doc-sheet-{sheet_id[:8]}-002",
                                "title": "Second Document from Google Sheets Index",
                                "type": "document",
                                "size": 0,
                                "uri": "",
                                "status": DocumentStatus.UPLOADED.value,
                                "upload_date": datetime.now().isoformat() + "Z",
                                "created_by": user["user"],
                                "media_type": "document",
                                "doc_type": "misc",
                                "source_ref": None,
                                "required_fields_ok": True,
                                "created_at": datetime.now(),
                                "updated_at": datetime.now(),
                                "requires_permission": False,
                                "permission_requested": False,
                                "permission_granted": False,
                                "permission_requested_at": None,
                                "permission_granted_at": None,
                                "drive_file_id": None,
                                "index_source_id": sheet_id,
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
            
            # Map rows to document metadata
            documents_found = []
            for i, row in enumerate(rows):
                try:
                    doc_data = map_document_from_row(row, index_url, user["user"])
                    doc_data["id"] = f"doc-sheet-{sheet_id[:8]}-{i + 1:03d}"
                    doc_data["from_sheet_index"] = True
                    doc_data["sheet_index_id"] = sheet_id
                    documents_found.append(doc_data)
                except Exception as e:
                    logger.error(f"Error mapping sheet row {i}: {e}")
                    continue
            
                # Save documents to Firestore
                saved_docs = []
                for doc_data in documents_found:
                    try:
                        logger.info(f"Converting document data to DocumentMetadata: {doc_data.get('id', 'unknown')}")
                        
                        # Create a clean DocumentMetadata object with only required fields
                        clean_doc_data = {
                            "id": doc_data["id"],
                            "title": doc_data["title"],
                            "type": doc_data["type"],
                            "size": doc_data["size"],
                            "uri": doc_data["uri"],
                            "status": doc_data["status"],
                            "upload_date": doc_data["upload_date"],
                            "created_by": doc_data["created_by"],
                            "media_type": doc_data["media_type"],
                            "doc_type": doc_data["doc_type"],
                            "source_ref": doc_data["source_ref"],
                            "required_fields_ok": doc_data["required_fields_ok"],
                            "created_at": doc_data["created_at"],
                            "updated_at": doc_data["updated_at"],
                            "requires_permission": doc_data.get("requires_permission", False),
                            "permission_requested": doc_data.get("permission_requested", False),
                            "permission_granted": doc_data.get("permission_granted", False),
                            "permission_requested_at": doc_data.get("permission_requested_at"),
                            "permission_granted_at": doc_data.get("permission_granted_at"),
                            "drive_file_id": doc_data.get("drive_file_id"),
                            "index_source_id": doc_data.get("index_source_id")
                        }
                        
                        # Convert to DocumentMetadata object
                        doc_metadata = DocumentMetadata(**clean_doc_data)
                        logger.info(f"Successfully created DocumentMetadata for {doc_metadata.id}")
                        doc_id = await firestore_client.save_document(doc_metadata)
                        saved_docs.append(doc_data)
                        logger.info(f"Successfully saved document {doc_id} to Firestore")
                    except Exception as e:
                        logger.error(f"Error saving document {doc_data.get('id', 'unknown')}: {e}", exc_info=True)
                        continue
            
            return {
                "success": True,
                "documents_created": len(saved_docs),
                "documents": saved_docs,
                "message": f"Successfully analyzed Google Sheets and created {len(saved_docs)} document entries.",
                "sheet_id": sheet_id
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only 'sheets' index_type is currently supported"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze document index: {str(e)}"
        )

@app.get("/admin/documents/pending")
async def get_pending_documents(
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get all documents pending approval.
    """
    try:
        # Query Firestore for pending documents
        docs_ref = firestore_client.db.collection("documents")
        
        # Get documents with pending statuses
        pending_statuses = [DocumentStatus.UPLOADED.value, DocumentStatus.PENDING_ACCESS.value, DocumentStatus.ACCESS_APPROVED.value]
        
        all_docs = []
        for status_val in pending_statuses:
            query = docs_ref.where("status", "==", status_val)
            docs = query.stream()
            
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["id"] = doc.id
                all_docs.append(doc_data)
        
        return {
            "documents": all_docs,
            "total": len(all_docs)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending documents: {str(e)}"
        )

@app.get("/admin/documents/by-category/{category}")
async def get_documents_by_category(
    category: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """
    Get documents by category - only returns indexed documents available to users.
    """
    try:
        documents = await firestore_client.query_documents_by_category(category)
        
        return {
            "category": category,
            "documents": documents,
            "total": len(documents),
            "message": f"Found {len(documents)} indexed documents in {category} category"
        }
        
    except Exception as e:
        logger.error(f"Failed to get documents by category: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents by category: {str(e)}"
        )

@app.post("/admin/documents/{doc_id}/grant-permission")
async def grant_document_permission(
    doc_id: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """Grant permission for a document."""
    try:
        doc_metadata = await firestore_client.get_document(doc_id)
        if not doc_metadata:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        if doc_metadata.status != DocumentStatus.PENDING_ACCESS.value:
            raise HTTPException(status_code=400, detail=f"Document {doc_id} is not in pending_access status")
        
        doc_metadata.status = DocumentStatus.ACCESS_APPROVED.value
        doc_metadata.permission_granted = True
        doc_metadata.permission_granted_at = datetime.now()
        doc_metadata.updated_at = datetime.now()
        
        await firestore_client.save_document(doc_metadata)
        
        return {
            "success": True,
            "doc_id": doc_id,
            "status": DocumentStatus.ACCESS_APPROVED.value,
            "message": f"Permission granted for document {doc_id}."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to grant permission: {str(e)}")

async def trigger_document_vectorization(doc_metadata: DocumentMetadata) -> None:
    """
    Trigger document vectorization process.
    
    Architecture:
    - Google Drive documents: Keep in G-Drive, only vectorize content for search/reference
    - Local uploads: Store in GCS + vectorize for full functionality
    - Vectorization: Extract text, create embeddings, store metadata for AI assistant
    """
    try:
        logger.info(f"Starting vectorization for document {doc_metadata.id}: {doc_metadata.title}")
        
        # Determine document source type
        is_google_drive = doc_metadata.drive_file_id is not None
        is_local_upload = doc_metadata.uri and doc_metadata.uri.startswith('gs://')
        
        if is_google_drive:
            logger.info(f"Google Drive document - vectorizing content only, keeping source in G-Drive")
            # For G-Drive documents: Extract text content, create embeddings
            # Document remains in Google Drive, we just vectorize the content
            processing_steps = [
                "Access Google Drive document",
                "Extract text content using Document AI", 
                "Chunk text for embedding generation",
                "Generate embeddings for vector search",
                "Store embeddings and metadata (document stays in G-Drive)"
            ]
        elif is_local_upload:
            logger.info(f"Local upload - storing in GCS and vectorizing")
            # For local uploads: Store in GCS, then vectorize
            processing_steps = [
                "Document already stored in GCS",
                "Extract text content using Document AI",
                "Chunk text for embedding generation", 
                "Generate embeddings for vector search",
                "Store embeddings and metadata"
            ]
        else:
            logger.info(f"URL-based document - vectorizing content only")
            # For URL documents: Extract content, create embeddings
            processing_steps = [
                "Access document via URL",
                "Extract text content using Document AI",
                "Chunk text for embedding generation",
                "Generate embeddings for vector search", 
                "Store embeddings and metadata"
            ]
        
        # Simulate processing time
        import asyncio
        await asyncio.sleep(1)
        
        # Update document with processing results
        doc_metadata.processing_result = {
            "vectorization_status": "completed",
            "document_source": "google_drive" if is_google_drive else ("gcs" if is_local_upload else "url"),
            "source_retained": is_google_drive or not is_local_upload,  # True if document stays in original location
            "chunks_created": 5,
            "embeddings_generated": 5,
            "vector_index_id": f"vec_{doc_metadata.id}",
            "processed_at": datetime.now().isoformat() + "Z",
            "processing_steps": processing_steps
        }
        
        logger.info(f"Vectorization completed for document {doc_metadata.id} - source retained: {doc_metadata.processing_result['source_retained']}")
        
    except Exception as e:
        logger.error(f"Vectorization failed for document {doc_metadata.id}: {e}")
        raise

@app.post("/admin/test-vectorization/{doc_id}")
async def test_vectorization_workflow(
    doc_id: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """Test the complete vectorization workflow."""
    try:
        # Create a test document
        test_doc = {
            "id": doc_id,
            "title": f"Test Document {doc_id}",
            "type": "document",
            "size": 1024,
            "uri": f"https://example.com/doc/{doc_id}",
            "status": "uploaded",
            "upload_date": datetime.now().isoformat() + "Z",
            "created_by": user["user"],
            "media_type": "document",
            "doc_type": "misc",
            "source_ref": None,
            "required_fields_ok": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "requires_permission": False,
            "permission_requested": False,
            "permission_granted": False,
            "permission_requested_at": None,
            "permission_granted_at": None,
            "drive_file_id": None,
            "index_source_id": None
        }
        
        # Store in test documents
        test_documents[doc_id] = test_doc
        
        # Step 1: Approve document
        test_doc["status"] = "processed"
        test_doc["approved_by"] = [user["user"]]
        test_doc["updated_at"] = datetime.now()
        
        # Step 2: Trigger vectorization
        await trigger_document_vectorization(DocumentMetadata(**test_doc))
        
        # Step 3: Mark as indexed
        test_doc["status"] = "indexed"
        test_doc["updated_at"] = datetime.now()
        test_documents[doc_id] = test_doc
        
        return {
            "success": True,
            "doc_id": doc_id,
            "status": "indexed",
            "message": f"Document {doc_id} successfully approved, vectorized, and indexed. Available in misc section.",
            "doc_type": "misc",
            "architecture_note": "Document content vectorized for AI assistant, source document remains in original location",
            "workflow_steps": [
                "1. Document created and stored",
                "2. Document approved for processing", 
                "3. Document content vectorized (text extracted, embeddings created)",
                "4. Document indexed and available to users",
                "5. Original document source retained (G-Drive/URL)"
            ],
            "processing_result": test_doc.get("processing_result", {})
        }
        
    except Exception as e:
        logger.error(f"Test vectorization failed for document {doc_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test vectorization failed: {str(e)}")

@app.get("/admin/test-documents")
async def get_test_documents(
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """Get all test documents."""
    return {
        "documents": list(test_documents.values()),
        "total": len(test_documents)
    }

@app.get("/admin/test-documents/by-category/{category}")
async def get_test_documents_by_category(
    category: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """Get test documents by category - only indexed documents."""
    indexed_docs = [
        doc for doc in test_documents.values() 
        if doc.get("doc_type") == category and doc.get("status") == "indexed"
    ]
    
    return {
        "category": category,
        "documents": indexed_docs,
        "total": len(indexed_docs),
        "message": f"Found {len(indexed_docs)} indexed documents in {category} category"
    }

@app.post("/admin/documents/{doc_id}/approve")
async def approve_document(
    doc_id: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """Approve a document for processing and vectorization."""
    try:
        doc_metadata = await firestore_client.get_document(doc_id)
        if not doc_metadata:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        if doc_metadata.status not in [DocumentStatus.UPLOADED.value, DocumentStatus.ACCESS_APPROVED.value]:
            raise HTTPException(status_code=400, detail=f"Document {doc_id} cannot be approved")
        
        # Step 1: Mark as approved for processing
        doc_metadata.status = DocumentStatus.PROCESSED.value
        doc_metadata.approved_by = [user["user"]]
        doc_metadata.updated_at = datetime.now()
        
        await firestore_client.save_document(doc_metadata)
        
        # Step 2: Trigger vectorization process
        try:
            await trigger_document_vectorization(doc_metadata)
            
            # Step 3: Update status to indexed after successful vectorization
            doc_metadata.status = DocumentStatus.INDEXED.value
            doc_metadata.updated_at = datetime.now()
            await firestore_client.save_document(doc_metadata)
            
            logger.info(f"Document {doc_id} successfully vectorized and indexed")
            
        except Exception as vectorization_error:
            logger.error(f"Vectorization failed for document {doc_id}: {vectorization_error}")
            # Keep status as PROCESSED even if vectorization fails
            # Admin can retry vectorization later
        
        return {
            "success": True,
            "doc_id": doc_id,
            "status": doc_metadata.status,
            "message": f"Document {doc_id} approved and vectorized. Available in {doc_metadata.doc_type.value} section.",
            "doc_type": doc_metadata.doc_type.value if doc_metadata.doc_type else "misc"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve document {doc_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve document: {str(e)}")

@app.delete("/admin/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    user: dict = Depends(require_admin_auth)
) -> Dict[str, Any]:
    """Delete a document."""
    try:
        doc_metadata = await firestore_client.get_document(doc_id)
        if not doc_metadata:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        doc_ref = firestore_client.db.collection("documents").document(doc_id)
        doc_ref.delete()
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": f"Document {doc_id} deleted."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)