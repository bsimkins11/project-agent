#!/bin/bash

# Minimal deployment script for Project Agent
# This deploys just the essential services for document ingestion

set -e

PROJECT_ID="transparent-agent-test"
REGION="us-central1"

echo "🚀 Starting minimal deployment for document ingestion..."

# Deploy chat API
echo "📡 Deploying Chat API..."
gcloud run deploy project-agent-chat-api \
  --source services/api/chat \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8081 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "GCP_PROJECT=$PROJECT_ID,REGION=$REGION,GCS_DOC_BUCKET=ta-test-docs-uat,GCS_THUMB_BUCKET=ta-test-thumbs-uat,FIRESTORE_DB=(default),VECTOR_INDEX=89915861896265728,NODE_ENV=production"

# Deploy upload API
echo "📤 Deploying Upload API..."
gcloud run deploy project-agent-upload-api \
  --source services/api/upload \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8085 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "GCP_PROJECT=$PROJECT_ID,REGION=$REGION,GCS_DOC_BUCKET=ta-test-docs-uat,GCS_THUMB_BUCKET=ta-test-thumbs-uat,FIRESTORE_DB=(default),NODE_ENV=production"

# Deploy inventory API
echo "📋 Deploying Inventory API..."
gcloud run deploy project-agent-inventory-api \
  --source services/api/inventory \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8082 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "GCP_PROJECT=$PROJECT_ID,REGION=$REGION,GCS_DOC_BUCKET=ta-test-docs-uat,GCS_THUMB_BUCKET=ta-test-thumbs-uat,FIRESTORE_DB=(default),NODE_ENV=production"

echo "✅ Minimal deployment completed!"
echo ""
echo "🌐 Your services are now available at:"
echo "  Chat API: https://project-agent-chat-api-$PROJECT_ID.a.run.app"
echo "  Upload API: https://project-agent-upload-api-$PROJECT_ID.a.run.app"
echo "  Inventory API: https://project-agent-inventory-api-$PROJECT_ID.a.run.app"
echo ""
echo "🧪 Ready for document ingestion testing!"
