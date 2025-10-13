"""Hybrid Google Sheets client - tries user OAuth, falls back to service account."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class HybridSheetsClient:
    """
    Hybrid Sheets client that tries user OAuth first, then service account.
    
    This provides the best UX - no sharing needed for user's own sheets,
    while maintaining backward compatibility with service account for shared sheets.
    
    Security benefits:
    - User-scoped access (principle of least privilege)
    - Token expiration (OAuth tokens expire in ~1 hour)
    - Clear audit trail (user attribution)
    - Revocable access (via Google account settings)
    """
    
    def __init__(
        self, 
        user_credentials: Optional[Credentials] = None,
        service_account_credentials: Optional[Credentials] = None,
        service_account_email: str = ""
    ):
        """
        Initialize hybrid client with optional user and service account credentials.
        
        Args:
            user_credentials: User's OAuth credentials (preferred)
            service_account_credentials: Service account credentials (fallback)
            service_account_email: Service account email for error messages
        """
        self.user_credentials = user_credentials
        self.service_account_credentials = service_account_credentials
        self.service_account_email = service_account_email
        
    async def parse_sheet(
        self, 
        sheet_id: str, 
        gid: int = 0
    ) -> Tuple[List[Dict[str, Any]], str, str]:
        """
        Parse Google Sheets, trying user OAuth first, then service account.
        
        Args:
            sheet_id: Google Sheets document ID
            gid: Sheet tab ID (0 for first tab)
            
        Returns:
            Tuple of (rows, sheet_name, auth_method)
            - rows: List of row dictionaries
            - sheet_name: Name of the sheet tab
            - auth_method: "user_oauth", "service_account", or "failed"
            
        Raises:
            Exception: If both authentication methods fail
        """
        errors = []
        
        # Strategy 1: Try User OAuth first (best UX, best security)
        if self.user_credentials:
            try:
                logger.info(f"Attempting to access sheet {sheet_id} with user OAuth")
                rows, sheet_name = await self._parse_with_credentials(
                    sheet_id, gid, self.user_credentials
                )
                logger.info(
                    f"✅ Success with user OAuth - no sharing needed! "
                    f"Retrieved {len(rows)} rows from '{sheet_name}'"
                )
                return rows, sheet_name, "user_oauth"
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"User OAuth failed: {error_msg}")
                errors.append(f"User OAuth: {error_msg}")
                # Continue to try service account
        
        # Strategy 2: Fallback to Service Account
        if self.service_account_credentials:
            try:
                logger.info(f"Attempting to access sheet {sheet_id} with service account")
                rows, sheet_name = await self._parse_with_credentials(
                    sheet_id, gid, self.service_account_credentials
                )
                logger.info(
                    f"✅ Success with service account. "
                    f"Retrieved {len(rows)} rows from '{sheet_name}'"
                )
                return rows, sheet_name, "service_account"
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Service account failed: {error_msg}")
                errors.append(f"Service account: {error_msg}")
        
        # Both methods failed - provide helpful error message
        error_detail = self._build_error_message(errors)
        raise Exception(error_detail)
    
    def _build_error_message(self, errors: List[str]) -> str:
        """Build helpful error message with troubleshooting steps."""
        error_msg = "Unable to access Google Sheets.\n\n"
        
        if self.user_credentials and self.service_account_credentials:
            # Both methods tried
            error_msg += "❌ Both authentication methods failed:\n"
            for error in errors:
                error_msg += f"  • {error}\n"
            error_msg += "\n"
        
        error_msg += "📝 How to fix:\n\n"
        
        if self.user_credentials:
            error_msg += "Option 1 (Recommended): Check your Google permissions\n"
            error_msg += "  1. Make sure you have access to this Google Sheet\n"
            error_msg += "  2. Try opening the sheet in a new tab to verify\n"
            error_msg += "  3. If you don't have access, ask the owner to share it with you\n\n"
        
        if self.service_account_credentials:
            error_msg += f"Option 2: Share with the service account\n"
            error_msg += f"  1. Open your Google Sheet\n"
            error_msg += f"  2. Click the 'Share' button\n"
            error_msg += f"  3. Add this email: {self.service_account_email}\n"
            error_msg += f"  4. Set permission to 'Viewer'\n"
            error_msg += f"  5. Click 'Send'\n"
            error_msg += f"  6. Try again\n\n"
        
        error_msg += "💡 Tip: You only need to share once. Access is retained forever."
        
        return error_msg
    
    async def _parse_with_credentials(
        self, 
        sheet_id: str, 
        gid: int, 
        credentials: Credentials
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Parse sheet with given credentials.
        
        Args:
            sheet_id: Google Sheets document ID
            gid: Sheet tab ID
            credentials: OAuth or service account credentials
            
        Returns:
            Tuple of (rows, sheet_name)
            
        Raises:
            HttpError: If API call fails
            Exception: For other errors
        """
        try:
            # Build Sheets API service
            service = build('sheets', 'v4', credentials=credentials)
            
            # Convert gid to int if it's a string
            if isinstance(gid, str):
                gid = int(gid) if gid.isdigit() else 0
            
            # Get sheet name from GID
            sheet_name = "Sheet1"  # Default
            if gid > 0:
                try:
                    spreadsheet = service.spreadsheets().get(
                        spreadsheetId=sheet_id
                    ).execute()
                    
                    for sheet in spreadsheet.get('sheets', []):
                        sheet_props = sheet.get('properties', {})
                        if sheet_props.get('sheetId') == gid:
                            sheet_name = sheet_props.get('title', f'Sheet{gid}')
                            break
                except HttpError as e:
                    # If we can't get sheet metadata, use default name
                    logger.warning(f"Could not get sheet metadata: {e}")
            
            # Get sheet data
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=sheet_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return [], sheet_name
            
            # Convert to list of dicts
            headers = values[0]
            rows = []
            for row_values in values[1:]:
                row_dict = {}
                for i, header in enumerate(headers):
                    row_dict[header] = row_values[i] if i < len(row_values) else ""
                rows.append(row_dict)
            
            return rows, sheet_name
            
        except HttpError as e:
            # Extract meaningful error message
            error_details = e.error_details if hasattr(e, 'error_details') else []
            if e.resp.status == 403:
                raise Exception(
                    f"Permission denied. You don't have access to this Google Sheet. "
                    f"Status: {e.resp.status}"
                )
            elif e.resp.status == 404:
                raise Exception(
                    f"Google Sheet not found. Check the URL is correct. "
                    f"Status: {e.resp.status}"
                )
            else:
                raise Exception(
                    f"Google Sheets API error: {e.resp.status} - {e.reason}"
                )
        except Exception as e:
            # Re-raise with context
            raise Exception(f"Failed to parse Google Sheet: {str(e)}")
    
    def get_auth_info(self) -> Dict[str, Any]:
        """
        Get information about available authentication methods.
        
        Returns:
            Dictionary with auth status
        """
        return {
            "user_oauth_available": self.user_credentials is not None,
            "service_account_available": self.service_account_credentials is not None,
            "service_account_email": self.service_account_email,
            "preferred_method": "user_oauth" if self.user_credentials else "service_account"
        }

