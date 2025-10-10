"""Google Cloud Storage client for Project Agent."""

import os
from typing import Optional
from google.cloud import storage


class GCSClient:
    """Client for Google Cloud Storage operations."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.client = storage.Client(project=self.project_id)
    
    async def upload_file(self, bucket_name: str, file_path: str, file_content: bytes, content_type: str = None) -> str:
        """Upload file to GCS."""
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(file_path)
            
            # For text-based files, use text/plain to avoid content-type conflicts
            if content_type and content_type.startswith('text/'):
                blob.content_type = 'text/plain'
            elif content_type:
                blob.content_type = content_type
            
            blob.upload_from_string(file_content)
            return blob.public_url
        except Exception as e:
            print(f"Error uploading file to GCS: {e}")
            raise
    
    async def download_file(self, gcs_uri: str) -> bytes:
        """Download file from GCS."""
        try:
            # Handle both gs:// URIs and public URLs
            if gcs_uri.startswith("gs://"):
                # gs://bucket-name/path/to/file
                parts = gcs_uri[5:].split("/", 1)
                bucket_name = parts[0]
                filename = parts[1] if len(parts) > 1 else ""
            elif "storage.googleapis.com" in gcs_uri:
                # https://storage.googleapis.com/bucket-name/path/to/file
                parts = gcs_uri.split("storage.googleapis.com/")[1].split("/", 1)
                bucket_name = parts[0]
                filename = parts[1] if len(parts) > 1 else ""
            else:
                raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
            
            if not bucket_name:
                raise ValueError("Cannot determine bucket name from URI")
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(filename)
            return blob.download_as_bytes()
            
        except Exception as e:
            print(f"Error downloading file from GCS: {e}")
            raise
    
    async def get_signed_url(self, gcs_uri: str, method: str = "GET") -> str:
        """Get signed URL for GCS object."""
        try:
            # Handle both gs:// URIs and public URLs
            if gcs_uri.startswith("gs://"):
                # gs://bucket-name/path/to/file
                parts = gcs_uri[5:].split("/", 1)
                bucket_name = parts[0]
                filename = parts[1] if len(parts) > 1 else ""
            elif "storage.googleapis.com" in gcs_uri:
                # https://storage.googleapis.com/bucket-name/path/to/file
                parts = gcs_uri.split("storage.googleapis.com/")[1].split("/", 1)
                bucket_name = parts[0]
                filename = parts[1] if len(parts) > 1 else ""
            else:
                raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
            
            if not bucket_name:
                raise ValueError("Cannot determine bucket name from URI")
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(filename)
            
            return blob.generate_signed_url(
                version="v4",
                expiration=3600,  # 1 hour
                method=method
            )
            
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            raise
    
    async def get_document_content(self, gcs_uri: str) -> Optional[str]:
        """Get document text content."""
        try:
            content = await self.download_file(gcs_uri)
            # For now, return as string - in production, parse based on file type
            return content.decode('utf-8', errors='ignore')
        except Exception:
            return None
