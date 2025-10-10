"""Firestore client for Project Agent."""

import os
from typing import Dict, Any, List, Optional
from google.cloud import firestore
from packages.shared.schemas import DocumentMetadata, InventoryFilters, InventoryResponse


class FirestoreClient:
    """Client for Firestore operations."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.db = firestore.Client(project=self.project_id)
    
    async def save_document(self, metadata: DocumentMetadata) -> str:
        """Save document metadata to Firestore."""
        try:
            doc_ref = self.db.collection("documents").document(metadata.id)
            doc_ref.set(metadata.dict())
            return metadata.id
        except Exception as e:
            print(f"Error saving document to Firestore: {e}")
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
    
    async def save_document_metadata(self, metadata: DocumentMetadata):
        """Legacy method - use save_document instead."""
        return await self.save_document(metadata)
    
    async def get_document_metadata(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Legacy method - use get_document instead."""
        return await self.get_document(doc_id)
    
    async def get_inventory(self, filters: Optional[InventoryFilters], page: int, page_size: int, sort_by: str, sort_order: str) -> Dict[str, Any]:
        """Get inventory with filtering and pagination."""
        # Placeholder implementation
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }
    
    async def get_document_chunks(self, doc_id: str) -> List[str]:
        """Get document text chunks."""
        # Placeholder implementation
        return []
    
    async def get_document_vectors(self, doc_id: str) -> List[str]:
        """Get document vector IDs."""
        # Placeholder implementation
        return []
    
    async def save_audit_entry(self, audit_entry: Dict[str, Any]):
        """Save audit entry."""
        doc_ref = self.db.collection("audit_logs").document()
        doc_ref.set(audit_entry)
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status."""
        doc_ref = self.db.collection("jobs").document(job_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    
    async def query_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Query documents by category/doc_type."""
        try:
            docs_ref = self.db.collection("documents")
            query = docs_ref.where("doc_type", "==", category)
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