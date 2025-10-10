# Google Service Account Setup Guide

This guide explains how to set up a Google Service Account for the Project Deliverable Agent to access private Google Drive documents and Google Sheets.

## Step 1: Create a Service Account

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **IAM & Admin** > **Service Accounts**
4. Click **Create Service Account**
5. Fill in the details:
   - **Service account name**: `project-agent-drive-access`
   - **Service account ID**: `project-agent-drive-access` (auto-generated)
   - **Description**: `Service account for Project Deliverable Agent to access Google Drive documents`
6. Click **Create and Continue**
7. Skip the optional steps and click **Done**

## Step 2: Generate Service Account Key

1. Find your newly created service account in the list
2. Click on the service account email
3. Go to the **Keys** tab
4. Click **Add Key** > **Create new key**
5. Select **JSON** format
6. Click **Create**
7. The JSON key file will be downloaded to your computer

## Step 3: Configure Required APIs

1. Go to **APIs & Services** > **Library**
2. Enable the following APIs:
   - **Google Drive API**
   - **Google Sheets API**
   - **Google Docs API** (if you plan to access Google Docs)

## Step 4: Set Up Service Account Credentials

### Option A: Environment Variable (Recommended for Cloud Run)

1. Open the downloaded JSON key file
2. Copy the entire JSON content
3. Set it as an environment variable in your Cloud Run service:
   ```bash
   gcloud run services update project-agent-admin-api \
     --region=us-central1 \
     --set-env-vars="GOOGLE_SERVICE_ACCOUNT_KEY='{\"type\":\"service_account\",\"project_id\":\"your-project\",...}'"
   ```

### Option B: Service Account File (For local development)

1. Copy the JSON key file to your project directory as `service-account-key.json`
2. Add it to `.gitignore` to prevent committing secrets
3. The application will automatically use this file when running locally

## Step 5: Grant Access to Documents

### For Google Sheets:
1. Open the Google Sheet you want to share
2. Click **Share** button
3. Add the service account email (found in the JSON key file under `client_email`)
4. Give it **Viewer** permissions
5. Click **Send**

### For Google Drive Folders:
1. Right-click on the folder in Google Drive
2. Select **Share**
3. Add the service account email
4. Give it **Viewer** permissions
5. Click **Send**

### For Individual Documents:
1. Open the document
2. Click **Share**
3. Add the service account email
4. Give it **Viewer** permissions
5. Click **Send**

## Step 6: Test the Integration

1. Deploy the updated admin API service
2. Check the service account status:
   ```bash
   curl -X GET "https://project-agent-admin-api-117860496175.us-central1.run.app/admin/service-account-status"
   ```
3. Try uploading a Google Sheets URL that the service account has access to

## Security Best Practices

1. **Never commit the JSON key file to version control**
2. **Use environment variables in production**
3. **Grant minimal required permissions** (Viewer only)
4. **Regularly rotate service account keys**
5. **Monitor service account usage** in Google Cloud Console

## Troubleshooting

### Service Account Not Working
- Verify the service account email is added to the document's sharing settings
- Check that the required APIs are enabled
- Ensure the JSON key is properly formatted
- Check the Cloud Run logs for authentication errors

### Permission Denied Errors
- Confirm the service account has access to the specific document
- Verify the document is not restricted by organizational policies
- Check that the service account has the correct scopes

### API Quota Exceeded
- Monitor API usage in Google Cloud Console
- Consider implementing rate limiting
- Use batch requests when possible

## Service Account Email Format

The service account email will look like:
```
project-agent-drive-access@your-project-id.iam.gserviceaccount.com
```

Use this email address when sharing documents with the service account.
