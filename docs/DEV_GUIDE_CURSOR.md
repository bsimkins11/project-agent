# Project Agent - Development Guide for Cursor

## Overview

This guide provides comprehensive instructions for developing the Project Agent system in Cursor. The system ingests documents and images, processes them through Google Cloud AI services, and provides a searchable knowledge base with cited answers.

## Architecture

- **Scope**: Documents + images only
- **Auth**: Restricted to @transparent.partners domain
- **Ingestion**: Google Drive sync, CSV upload, single links
- **Processing**: Document AI, Vision API, Vertex AI embeddings
- **Storage**: Vertex AI Vector Search, Firestore, GCS
- **UI**: Next.js portal with admin and user interfaces

## Prerequisites

### GCP Setup
- Project: `transparent-agent-test` (117860496175)
- APIs enabled: Document AI, Vision, Vertex AI, Firestore, Storage, Pub/Sub, Cloud Scheduler, Secret Manager, Identity Platform, Drive & Sheets

### Local Development Setup

1. **Authenticate to GCP**:
   ```bash
   gcloud auth application-default login
   gcloud config set project transparent-agent-test
   ```

2. **Environment Configuration**:
   Create `/services/.env`:
   ```env
   GCP_PROJECT=transparent-agent-test
   REGION=us-central1
   ALLOWED_DOMAIN=transparent.partners
   GCS_DOC_BUCKET=ta-test-docs-dev
   GCS_THUMB_BUCKET=ta-test-thumbs-dev
   FIRESTORE_DB=(default)
   VECTOR_INDEX=project-agent-dev
   DOC_AI_PROCESSOR=projects/117860496175/locations/us/processors/<processor-id>
   GOOGLE_OAUTH_CLIENT_ID=...
   GOOGLE_OAUTH_CLIENT_SECRET=...
   ```

## Running Services Locally

In Cursor terminal (split panes):

```bash
# API services
uv run fastapi dev services/api/chat/app.py --port 8081
uv run fastapi dev services/api/inventory/app.py --port 8082
uv run fastapi dev services/api/documents/app.py --port 8083
uv run fastapi dev services/api/admin/app.py --port 8084

# Ingestion worker
uv run python services/workers/ingestion/worker.py

# Web (Next.js)
cd web/portal && npm i && npm run dev
```

## API Endpoints

### Chat API
- `POST /chat` - Get AI-powered answers with citations

### Inventory API
- `GET /inventory` - List documents with filtering

### Documents API
- `GET /documents/:id` - Get document details and metadata

### Admin API
- `POST /admin/ingest/csv` - Bulk upload via CSV
- `POST /admin/ingest/link` - Add single document
- `POST /admin/gdrive/sync` - Sync Google Drive folders

## Security & Governance

- Domain restriction: Only @transparent.partners emails allowed
- DLP scanning: Content scanned before indexing
- Quarantine: Failed DLP items quarantined
- Double approval: Deletion requires two admin approvals

## Performance SLOs
- Query latency: ≤5s
- Document ingest: ≤5m
- Image ingest: ≤2m
