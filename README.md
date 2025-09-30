# Project Agent - Transparent Partners

A document and image ingestion system with AI-powered search capabilities, restricted to @transparent.partners domain.

## Architecture

- **Frontend**: Next.js portal with user and admin interfaces
- **Backend**: Python FastAPI services with ADK for agent orchestration
- **Storage**: Vertex AI Vector Search, Firestore, Google Cloud Storage
- **Authentication**: Google OAuth via Identity Platform
- **Ingestion**: Google Drive sync, CSV upload, single link processing

## Quick Start

1. **Setup GCP Authentication**:
   ```bash
   gcloud auth application-default login
   gcloud config set project transparent-agent-test
   ```

2. **Install Dependencies**:
   ```bash
   # Python services
   cd services && uv sync
   
   # Web portal
   cd web/portal && npm install
   ```

3. **Configure Environment**:
   Copy `services/env.example` to `services/.env` and configure your GCP settings.

4. **Run Development Services**:
   ```bash
   make dev  # Starts all services
   ```

## Development

See [DEV_GUIDE_CURSOR.md](docs/DEV_GUIDE_CURSOR.md) for detailed development instructions.
