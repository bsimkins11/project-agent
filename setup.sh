#!/bin/bash

# Project Agent Setup Script
echo "🚀 Setting up Project Agent for Transparent Partners..."

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "🔐 Please authenticate with gcloud first:"
    echo "   gcloud auth application-default login"
    echo "   gcloud config set project transparent-agent-test"
    exit 1
fi

# Set the project
echo "📋 Setting GCP project to transparent-agent-test..."
gcloud config set project transparent-agent-test

# Setup environment file
if [ ! -f services/.env ]; then
    echo "⚙️  Creating environment file..."
    cp services/env.example services/.env
    echo "✅ Created services/.env - Please edit it with your configuration"
else
    echo "✅ Environment file already exists"
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd services
if command -v uv &> /dev/null; then
    uv sync
else
    echo "⚠️  uv not found. Installing uv..."
    pip install uv
    uv sync
fi
cd ..

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd web/portal
npm install
cd ../..

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit services/.env with your GCP configuration"
echo "2. Run 'make dev' to start development services"
echo "3. Visit http://localhost:3000 for the web portal"
echo "4. Visit http://localhost:8081/docs for API documentation"
echo ""
echo "For infrastructure setup:"
echo "1. Run 'make terraform-init' to initialize Terraform"
echo "2. Run 'make terraform-apply' to create GCP resources"
echo ""
echo "For deployment:"
echo "1. Run 'make deploy' to deploy to Cloud Run"
