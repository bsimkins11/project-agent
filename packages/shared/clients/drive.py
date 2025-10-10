"""Google Drive client for Project Agent."""

import os
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class DriveClient:
    """Client for Google Drive operations using admin OAuth tokens."""
    
    def __init__(self, user_credentials: Optional[Credentials] = None):
        self.user_credentials = user_credentials
        self.service = self._build_service()
    
    def _build_service(self):
        """Build Google Drive service with user OAuth credentials."""
        if not self.user_credentials:
            print("Warning: No user credentials provided for Drive access")
            return None
        
        try:
            return build('drive', 'v3', credentials=self.user_credentials)
        except Exception as e:
            print(f"Warning: Could not initialize Drive service: {e}")
            return None
    
    async def list_files(self, folder_id: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """List files in Drive folder."""
        if not self.service:
            return []
        
        try:
            files = []
            page_token = None
            
            while True:
                # List files in folder
                query = f"'{folder_id}' in parents and trashed=false"
                if not recursive:
                    query += " and mimeType != 'application/vnd.google-apps.folder'"
                
                results = self.service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink, parents)",
                    pageToken=page_token
                ).execute()
                
                items = results.get('files', [])
                files.extend(items)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            return files
            
        except HttpError as e:
            print(f"Error listing Drive files: {e}")
            return []
    
    async def download_file(self, file_id: str) -> bytes:
        """Download file from Drive."""
        if not self.service:
            return b""
        
        try:
            # Get file metadata first
            file_metadata = self.service.files().get(fileId=file_id).execute()
            
            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            file_content = request.execute()
            
            return file_content
            
        except HttpError as e:
            print(f"Error downloading Drive file: {e}")
            return b""
    
    async def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from Drive."""
        if not self.service:
            return None
        
        try:
            return self.service.files().get(fileId=file_id).execute()
        except HttpError as e:
            print(f"Error getting Drive file metadata: {e}")
            return None
