# How to Get the Service Account Email

## Quick Method: Use the API Endpoint

### 1. Call the endpoint:

```bash
curl -X GET "https://your-admin-api-url/admin/service-account-info" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Replace `your-admin-api-url` with your actual Admin API URL, such as:
- Local: `http://localhost:8084`
- Production: `https://project-agent-admin-api-117860496175.us-central1.run.app`

### 2. Response:

```json
{
  "service_account_email": "project-agent-drive-access@transparent-agent-test.iam.gserviceaccount.com",
  "instructions": {...},
  "note": "You only need to share documents once..."
}
```

### 3. Copy the `service_account_email` value

## Alternative: Check Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **IAM & Admin** → **Service Accounts**
3. Find the service account (e.g., `project-agent-drive-access`)
4. Copy the email address

## Alternative: Check Error Messages

When you get a "Failed to analyze document index" error, the error message now includes:
- 📧 The service account email
- 📝 Step-by-step sharing instructions

Just copy the email from the error message!

## What to Do with the Email

Once you have the service account email:

1. **Open your Google Sheet**
2. **Click "Share"** (top right)
3. **Paste the service account email**
4. **Set permission to "Viewer"**
5. **Click "Send"**

Done! The agent can now access your sheet.

## Example Service Account Emails

Your service account email will look like one of these:
```
project-agent-drive-access@transparent-agent-test.iam.gserviceaccount.com
sa-ingestor@transparent-agent-test.iam.gserviceaccount.com
your-sa-name@your-project-id.iam.gserviceaccount.com
```

## Testing

To verify the service account email is correct:
1. Share a test Google Sheet with the email
2. Try to analyze it in the Project Deliverable Agent
3. If it works, you have the correct email! ✅

## Need Help?

See these guides:
- **Quick Start**: `QUICK_START_SHARE_GOOGLE_SHEETS.md`
- **Detailed Setup**: `GOOGLE_SHEETS_SETUP_GUIDE.md`
- **Service Account Setup**: `SERVICE_ACCOUNT_SETUP.md`

