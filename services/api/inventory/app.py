"""Inventory API service for Project Agent."""

from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware

from packages.shared.schemas import InventoryRequest, InventoryResponse, InventoryFilters
from packages.shared.clients.firestore import FirestoreClient
from packages.shared.clients.auth import require_domain_auth

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
    user: dict = Depends(require_domain_auth)
) -> InventoryResponse:
    """
    Get document inventory with filtering and pagination.
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
        
        # Get inventory from Firestore
        result = await firestore.get_inventory(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return InventoryResponse(**result)
        
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
