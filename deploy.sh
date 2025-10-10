#!/bin/bash

# Project Agent Deployment Script
# This script deploys the entire Project Agent system to GCP

set -e

# Configuration
PROJECT_ID="transparent-agent-test"
REGION="us-central1"
ENVIRONMENT="uat"

echo "🚀 Starting Project Agent deployment to GCP..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Set the project
echo "📋 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Enable required APIs
echo "🔧 Enabling required GCP APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    documentai.googleapis.com \
    vision.googleapis.com \
    aiplatform.googleapis.com \
    firestore.googleapis.com \
    storage.googleapis.com \
    pubsub.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com \
    drive.googleapis.com \
    sheets.googleapis.com \
    dlp.googleapis.com

# Deploy infrastructure with Terraform
echo "🏗️  Deploying infrastructure with Terraform..."
cd infra/terraform

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    terraform init
fi

# Plan and apply infrastructure
terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="environment=$ENVIRONMENT"
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="environment=$ENVIRONMENT" -auto-approve

cd ../..

# Get infrastructure outputs
DOCS_BUCKET=$(terraform -chdir=infra/terraform output -raw documents_bucket)
THUMBS_BUCKET=$(terraform -chdir=infra/terraform output -raw thumbnails_bucket)
SERVICE_ACCOUNT=$(terraform -chdir=infra/terraform output -raw service_account_email)
VECTOR_INDEX=$(terraform -chdir=infra/terraform output -raw vector_index_name)

echo "📦 Infrastructure deployed:"
echo "  Documents bucket: $DOCS_BUCKET"
echo "  Thumbnails bucket: $THUMBS_BUCKET"
echo "  Service account: $SERVICE_ACCOUNT"
echo "  Vector index: $VECTOR_INDEX"

# Create environment file for services
echo "📝 Creating production environment configuration..."
cat > services/.env.production << EOF
# GCP Configuration
GCP_PROJECT=$PROJECT_ID
REGION=$REGION
ALLOWED_DOMAIN=transparent.partners

# Storage Buckets
GCS_DOC_BUCKET=$DOCS_BUCKET
GCS_THUMB_BUCKET=$THUMBS_BUCKET

# Database
FIRESTORE_DB=(default)

# AI Services
VECTOR_INDEX=$VECTOR_INDEX
DOC_AI_PROCESSOR=projects/$PROJECT_ID/locations/us/processors/<processor-id>

# Authentication
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

# Pub/Sub
PUBSUB_TOPIC_INGESTION=project-agent-ingestion
PUBSUB_SUBSCRIPTION_INGESTION=project-agent-ingestion-sub

# Service Account
SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT

# Admin emails (comma-separated)
ADMIN_EMAILS=admin@transparent.partners

# Environment
NODE_ENV=production
EOF

# Trigger Cloud Build deployment
echo "🏗️  Starting Cloud Build deployment..."
gcloud builds submit --config ops/cloudbuild.yaml .

echo "✅ Deployment completed!"
echo ""
echo "🌐 Your services are now available at:"
echo "  Web Portal: https://project-agent-web-$PROJECT_ID.a.run.app"
echo "  Chat API: https://project-agent-chat-api-$PROJECT_ID.a.run.app"
echo "  Upload API: https://project-agent-upload-api-$PROJECT_ID.a.run.app"
echo "  Inventory API: https://project-agent-inventory-api-$PROJECT_ID.a.run.app"
echo "  Documents API: https://project-agent-documents-api-$PROJECT_ID.a.run.app"
echo "  Admin API: https://project-agent-admin-api-$PROJECT_ID.a.run.app"
echo ""
echo "🧪 Next steps for UAT testing:"
echo "  1. Upload test documents via the web portal"
echo "  2. Test document search and chat functionality"
echo "  3. Verify all services are responding correctly"
echo "  4. Check Cloud Run logs for any issues"
echo ""
echo "📊 Monitor your deployment:"
echo "  Cloud Run: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "  Cloud Build: https://console.cloud.google.com/cloud-build?project=$PROJECT_ID"
echo "  Firestore: https://console.cloud.google.com/firestore?project=$PROJECT_ID"
echo "  Storage: https://console.cloud.google.com/storage?project=$PROJECT_ID"


