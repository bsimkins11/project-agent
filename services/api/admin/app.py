"""Admin API service for Project Agent."""

import csv
import io
from typing import List
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from packages.shared.schemas import (
    IngestRequest, IngestResponse, DriveSyncRequest, DriveSyncResponse
)
from packages.shared.clients.auth import require_admin_auth
from packages.shared.clients.pubsub import PubSubClient

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

# Initialize PubSub client
pubsub = PubSubClient()


@app.post("/admin/ingest/link", response_model=IngestResponse)
async def ingest_link(
    request: IngestRequest,
    user: dict = Depends(require_admin_auth)
) -> IngestResponse:
    """
    Ingest a single document from a link.
    """
    try:
        # Enqueue ingestion job
        job_id = await pubsub.publish_ingestion_job({
            "action": "link_ingest",
            "title": request.title,
            "doc_type": request.doc_type,
            "source_uri": request.source_uri,
            "tags": request.tags,
            "owner": request.owner,
            "version": request.version,
            "created_by": user["email"]
        })
        
        return IngestResponse(
            ok=True,
            job_id=job_id,
            message=f"Document ingestion job {job_id} queued successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Link ingestion failed: {str(e)}"
        )


@app.post("/admin/ingest/csv", response_model=IngestResponse)
async def ingest_csv(
    file: UploadFile = File(..., description="CSV file with document data"),
    user: dict = Depends(require_admin_auth)
) -> IngestResponse:
    """
    Bulk ingest documents from CSV file.
    
    Expected CSV columns: title, doc_type, source_uri, owner, version, tags, approved
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a CSV file"
            )
        
        # Read and parse CSV
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty or invalid"
            )
        
        # Enqueue jobs for each row
        job_ids = []
        for row in rows:
            job_id = await pubsub.publish_ingestion_job({
                "action": "csv_row",
                "title": row["title"],
                "doc_type": row["doc_type"],
                "source_uri": row["source_uri"],
                "owner": row.get("owner"),
                "version": row.get("version"),
                "tags": row.get("tags", "").split(",") if row.get("tags") else [],
                "created_by": user["email"]
            })
            job_ids.append(job_id)
        
        return IngestResponse(
            ok=True,
            count=len(job_ids),
            message=f"Queued {len(job_ids)} documents for ingestion"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV ingestion failed: {str(e)}"
        )


@app.post("/admin/gdrive/sync", response_model=DriveSyncResponse)
async def sync_google_drive(
    request: DriveSyncRequest,
    user: dict = Depends(require_admin_auth)
) -> DriveSyncResponse:
    """
    Sync documents from Google Drive folders.
    """
    try:
        # Enqueue Drive sync job
        job_id = await pubsub.publish_ingestion_job({
            "action": "gdrive_sync",
            "folder_ids": request.folder_ids,
            "recursive": request.recursive,
            "initiated_by": user["email"]
        })
        
        return DriveSyncResponse(
            ok=True,
            job_id=job_id,
            folders_processed=len(request.folder_ids),
            files_found=0  # Will be updated by worker
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drive sync failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "admin-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
