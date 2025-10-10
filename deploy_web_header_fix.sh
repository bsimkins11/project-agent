#!/bin/bash

# Quick Web Portal Deployment Script - Header Fix
# This script deploys ONLY the web portal with header fixes to GCP

set -e

# Configuration
PROJECT_ID="transparent-agent-test"
REGION="us-central1"

echo "🚀 Deploying Web Portal Header Fix..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

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

# Trigger Cloud Build for web portal only
echo "🏗️  Starting Cloud Build deployment for Web Portal..."
gcloud builds submit --config ops/cloudbuild-web-only.yaml .

echo "✅ Web Portal deployment completed!"
echo ""
echo "🌐 Your web portal is now available at:"
echo "  https://project-agent-web-117860496175.us-central1.run.app"
echo ""
echo "🔍 Changes deployed:"
echo "  ✓ Header now appears on admin page"
echo "  ✓ Authentication check includes auth_token from admin page"
echo "  ✓ Documents dropdown visible on all pages"
echo "  ✓ Home link visible on admin page for easy navigation"
echo "  ✓ Sign Out button visible on all authenticated pages"
echo ""
echo "🧪 Test the changes:"
echo "  1. Visit the admin page: https://project-agent-web-117860496175.us-central1.run.app/admin"
echo "  2. Verify the header appears with logo, title, and navigation"
echo "  3. Test the Documents dropdown"
echo "  4. Test the Home link to navigate back to chat"
echo "  5. Test the Sign Out button"
echo ""
echo "📊 Monitor your deployment:"
echo "  Cloud Run: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "  Cloud Build: https://console.cloud.google.com/cloud-build?project=$PROJECT_ID"

