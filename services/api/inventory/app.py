"""Inventory API service for Project Agent with RBAC filtering."""

from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware

from packages.shared.schemas import InventoryRequest, InventoryResponse, InventoryFilters
from packages.shared.clients.firestore import FirestoreClient
from packages.shared.clients.auth import require_domain_auth, filter_documents_by_access

app = FastAPI(
    title="Project Agent Inventory API",
    description="Document inventory and search service",
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
firestore = FirestoreClient()


@app.get("/inventory", response_model=InventoryResponse)
async def get_inventory(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    media_type: Optional[str] = Query(None, description="Filter by media type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    q: Optional[str] = Query(None, description="Search query"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    topics: Optional[str] = Query(None, description="Comma-separated topics"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    user: dict = Depends(require_domain_auth)
) -> InventoryResponse:
    """
    Get document inventory with filtering, pagination, and RBAC access control.
    Users see only documents they have access to based on their project/client assignments.
    """
    try:
        # Parse topics if provided
        topic_list = topics.split(",") if topics else None
        
        # Build filters
        filters = InventoryFilters(
            doc_type=doc_type,
            media_type=media_type,
            status=status,
            q=q,
            created_by=created_by,
            topics=topic_list
        )
        
        # Get all documents from Firestore (without pagination first)
        # We need all results to apply RBAC filtering before paginating
        all_results = await firestore.get_inventory(
            filters=filters,
            page=1,
            page_size=1000,  # Get a large batch
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Filter documents by user access (RBAC)
        accessible_docs = await filter_documents_by_access(
            user["email"],
            all_results["items"]
        )
        
        # Additional filtering by project_id or client_id if provided
        if project_id:
            accessible_docs = [d for d in accessible_docs if d.get("project_id") == project_id]
        if client_id:
            accessible_docs = [d for d in accessible_docs if d.get("client_id") == client_id]
        
        # Calculate pagination
        total = len(accessible_docs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_docs = accessible_docs[start_idx:end_idx]
        
        return InventoryResponse(
            items=paginated_docs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inventory retrieval failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "inventory-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
