"""Google Cloud Storage client for Project Agent."""

import os
from typing import Optional
from google.cloud import storage


class GCSClient:
    """Client for Google Cloud Storage operations."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.client = storage.Client(project=self.project_id)
    
    async def upload_file(self, content: bytes, bucket_name: str, filename: str):
        """Upload file to GCS."""
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_string(content)
    
    async def download_file(self, gcs_uri: str) -> bytes:
        """Download file from GCS."""
        bucket_name = gcs_uri.split("/")[2]
        filename = "/".join(gcs_uri.split("/")[3:])
        
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(filename)
        return blob.download_as_bytes()
    
    async def get_signed_url(self, gcs_uri: str, method: str = "GET") -> str:
        """Get signed URL for GCS object."""
        bucket_name = gcs_uri.split("/")[2]
        filename = "/".join(gcs_uri.split("/")[3:])
        
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        return blob.generate_signed_url(
            version="v4",
            expiration=3600,  # 1 hour
            method=method
        )
    
    async def get_document_content(self, gcs_uri: str) -> Optional[str]:
        """Get document text content."""
        try:
            content = await self.download_file(gcs_uri)
            # For now, return as string - in production, parse based on file type
            return content.decode('utf-8', errors='ignore')
        except Exception:
            return None
