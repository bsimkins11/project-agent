# Project Agent - Production Deployment Guide

This guide walks you through deploying the Project Agent system to Google Cloud Platform for User Acceptance Testing (UAT).

## 🚀 Quick Start

### Prerequisites

1. **Google Cloud SDK**: Install and authenticate
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   
   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Terraform**: Install Terraform for infrastructure management
   ```bash
   # macOS
   brew install terraform
   
   # Or download from https://terraform.io/downloads
   ```

3. **Docker**: Ensure Docker is running for container builds

### One-Command Deployment

```bash
# Make the deployment script executable and run it
chmod +x deploy.sh
./deploy.sh
```

This will:
- ✅ Enable all required GCP APIs
- ✅ Deploy infrastructure with Terraform
- ✅ Build and deploy all services to Cloud Run
- ✅ Configure environment variables
- ✅ Set up monitoring and logging

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js UI    │    │   FastAPI APIs  │    │  GCP Services   │
│                 │◄──►│                 │◄──►│                 │
│ - Chat Interface│    │ - Chat API      │    │ - Firestore     │
│ - Document Mgmt │    │ - Upload API    │    │ - Cloud Storage │
│ - Admin Panel   │    │ - Inventory API │    │ - Document AI   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Deployed Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Web Portal** | `https://project-agent-web-transparent-agent-test.a.run.app` | Main user interface |
| **Chat API** | `https://project-agent-chat-api-transparent-agent-test.a.run.app` | RAG-powered chat |
| **Upload API** | `https://project-agent-upload-api-transparent-agent-test.a.run.app` | Document upload |
| **Inventory API** | `https://project-agent-inventory-api-transparent-agent-test.a.run.app` | Document listing |
| **Documents API** | `https://project-agent-documents-api-transparent-agent-test.a.run.app` | Document details |
| **Admin API** | `https://project-agent-admin-api-transparent-agent-test.a.run.app` | Admin operations |

## 🧪 UAT Testing

### Automated Testing

Run the UAT test suite:

```bash
chmod +x test_uat.sh
./test_uat.sh
```

This will:
- ✅ Test all service health endpoints
- ✅ Upload a test document
- ✅ Test document search functionality
- ✅ Verify API responses
- ✅ Check web portal accessibility

### Manual Testing Checklist

1. **Document Upload**
   - [ ] Upload a PDF document via web interface
   - [ ] Upload a Word document (.docx)
   - [ ] Upload a text file (.txt)
   - [ ] Verify documents appear in inventory

2. **Document Search**
   - [ ] Search for uploaded documents in chat
   - [ ] Verify search results include citations
   - [ ] Test different search queries
   - [ ] Check response accuracy

3. **Admin Panel**
   - [ ] Access admin panel
   - [ ] View document inventory
   - [ ] Test document filtering
   - [ ] Verify document metadata

4. **Error Handling**
   - [ ] Upload unsupported file types
   - [ ] Upload oversized files
   - [ ] Test with invalid queries
   - [ ] Verify error messages

## 🔧 Configuration

### Environment Variables

The deployment automatically configures these environment variables:

```bash
# GCP Configuration
GCP_PROJECT=transparent-agent-test
REGION=us-central1
NODE_ENV=production

# Storage Buckets
GCS_DOC_BUCKET=ta-test-docs-dev
GCS_THUMB_BUCKET=ta-test-thumbs-dev

# Database
FIRESTORE_DB=(default)

# AI Services
VECTOR_INDEX=project-agent-dev
DOC_AI_PROCESSOR=projects/117860496175/locations/us/processors/<processor-id>
```

### Custom Configuration

To modify the deployment:

1. **Update Terraform variables** in `infra/terraform/main.tf`
2. **Modify Cloud Build** in `ops/cloudbuild.yaml`
3. **Update environment variables** in `deploy.sh`

## 📊 Monitoring and Logs

### Cloud Run Logs

View service logs:

```bash
# All services
gcloud logging read "resource.type=cloud_run_revision" --project=transparent-agent-test

# Specific service
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=project-agent-chat-api" --project=transparent-agent-test
```

### Cloud Console

- **Cloud Run**: https://console.cloud.google.com/run?project=transparent-agent-test
- **Cloud Build**: https://console.cloud.google.com/cloud-build?project=transparent-agent-test
- **Firestore**: https://console.cloud.google.com/firestore?project=transparent-agent-test
- **Storage**: https://console.cloud.google.com/storage?project=transparent-agent-test
- **Logging**: https://console.cloud.google.com/logs?project=transparent-agent-test

## 🚨 Troubleshooting

### Common Issues

1. **Service Not Starting**
   ```bash
   # Check logs
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME" --project=transparent-agent-test
   
   # Check service status
   gcloud run services describe SERVICE_NAME --region=us-central1 --project=transparent-agent-test
   ```

2. **Authentication Errors**
   ```bash
   # Re-authenticate
   gcloud auth login
   gcloud auth application-default login
   
   # Check service account permissions
   gcloud projects get-iam-policy transparent-agent-test
   ```

3. **Storage Access Issues**
   ```bash
   # Check bucket permissions
   gsutil iam get gs://ta-test-docs-dev
   
   # Test upload
   echo "test" | gsutil cp - gs://ta-test-docs-dev/test.txt
   ```

4. **Document AI Processing Failures**
   ```bash
   # Check processor status
   gcloud documentai processors list --location=us-central1 --project=transparent-agent-test
   
   # Test processor
   gcloud documentai processors process PROCESSOR_ID --location=us-central1 --project=transparent-agent-test
   ```

### Performance Optimization

1. **Scale Services**
   ```bash
   # Increase max instances
   gcloud run services update SERVICE_NAME --max-instances=20 --region=us-central1 --project=transparent-agent-test
   ```

2. **Optimize Memory**
   ```bash
   # Increase memory for processing services
   gcloud run services update project-agent-upload-api --memory=2Gi --region=us-central1 --project=transparent-agent-test
   ```

## 🔄 Updates and Maintenance

### Deploying Updates

1. **Code Changes**: Make your changes to the codebase
2. **Commit Changes**: `git add . && git commit -m "Update description"`
3. **Trigger Deployment**: `./deploy.sh`

### Rolling Back

```bash
# List previous revisions
gcloud run revisions list --service=SERVICE_NAME --region=us-central1 --project=transparent-agent-test

# Rollback to previous revision
gcloud run services update-traffic SERVICE_NAME --to-revisions=REVISION_NAME=100 --region=us-central1 --project=transparent-agent-test
```

## 📈 Scaling for Production

### High Availability

1. **Multi-Region Deployment**
   - Deploy to multiple regions
   - Use Cloud Load Balancing
   - Configure failover

2. **Database Optimization**
   - Enable Firestore multi-region
   - Configure backup policies
   - Set up monitoring alerts

3. **Security Hardening**
   - Enable IAM authentication
   - Configure VPC security
   - Set up DLP scanning

### Performance Tuning

1. **Caching**
   - Enable Cloud CDN
   - Configure Redis caching
   - Optimize database queries

2. **Monitoring**
   - Set up Cloud Monitoring
   - Configure alerting policies
   - Track key metrics

## 🎯 Next Steps

After successful UAT:

1. **Production Deployment**
   - Create production GCP project
   - Deploy with production configurations
   - Set up monitoring and alerting

2. **Security Implementation**
   - Enable Google OAuth authentication
   - Configure domain restrictions
   - Set up audit logging

3. **Performance Optimization**
   - Connect real Vector Search index
   - Implement caching strategies
   - Optimize document processing

4. **Feature Enhancements**
   - Google Drive integration
   - Advanced search filters
   - Batch operations
   - Analytics dashboard

## 📞 Support

For issues or questions:

1. **Check Logs**: Use Cloud Console logging
2. **Review Documentation**: Check this guide and code comments
3. **Test Locally**: Run services locally for debugging
4. **Monitor Metrics**: Use Cloud Monitoring dashboards

---

**Ready for Production UAT!** 🚀

The system is now deployed and ready for comprehensive testing. Use the automated test suite and manual testing checklist to verify all functionality before moving to production.

