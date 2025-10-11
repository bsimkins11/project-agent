#!/usr/bin/env python3
"""
Test script for Google Sheets parsing functionality.
This tests the improved Google Sheets analysis with better error handling.
"""

import requests
import csv
import io
import re
from typing import Dict, List, Optional

def extract_drive_file_id(url: str) -> Optional[str]:
    """Extract Google Drive file ID from URL."""
    patterns = [
        r'/file/d/([a-zA-Z0-9-_]+)',
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'/document/d/([a-zA-Z0-9-_]+)',
        r'/presentation/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def extract_gid_from_url(url: str) -> Optional[int]:
    """Extract GID from Google Sheets URL."""
    gid_match = re.search(r'[#&]gid=(\d+)', url)
    if gid_match:
        return int(gid_match.group(1))
    return None

def parse_google_sheets_csv(sheet_id: str, gid: int = 0) -> List[Dict[str, str]]:
    """Parse Google Sheets as CSV with improved error handling."""
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        print(f"Attempting to fetch CSV from URL: {csv_url}")
        response = requests.get(csv_url, timeout=30)
        response.raise_for_status()
        
        # Parse CSV
        csv_content = response.text
        
        # Check if we got valid CSV content
        if not csv_content.strip():
            raise Exception("Google Sheets appears to be empty or contains no data.")
        
        # Handle different CSV formats and encodings
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(csv_reader)
            
            if not rows:
                raise Exception("Google Sheets contains headers but no data rows.")
            
            print(f"Successfully parsed {len(rows)} rows from Google Sheets")
            return rows
            
        except csv.Error as csv_error:
            print(f"CSV parsing error: {csv_error}")
            raise Exception(f"Unable to parse Google Sheets data as CSV: {str(csv_error)}")
            
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error accessing Google Sheets: {e}")
        if e.response.status_code == 401:
            raise Exception("Google Sheets is not publicly accessible. Please change sharing settings to 'Anyone with the link can view' and try again.")
        elif e.response.status_code == 403:
            raise Exception("Access denied to Google Sheets. Please check sharing permissions.")
        elif e.response.status_code == 404:
            raise Exception("Google Sheets not found. Please verify the URL is correct and the sheet exists.")
        else:
            raise Exception(f"Failed to access Google Sheets (HTTP {e.response.status_code}): {str(e)}")
    except requests.exceptions.Timeout:
        raise Exception("Request timed out while accessing Google Sheets. Please try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error accessing Google Sheets: {str(e)}")
    except Exception as e:
        print(f"Unexpected error parsing Google Sheets: {e}")
        raise

def test_sheets_url(url: str):
    """Test a Google Sheets URL for document index analysis."""
    print(f"\n=== Testing Google Sheets URL ===")
    print(f"URL: {url}")
    
    # Extract sheet ID and GID
    sheet_id = extract_drive_file_id(url)
    if not sheet_id:
        print("❌ ERROR: Could not extract sheet ID from URL")
        return False
    
    gid = extract_gid_from_url(url)
    if gid is None:
        gid = 0
    
    print(f"Sheet ID: {sheet_id}")
    print(f"GID: {gid}")
    
    try:
        # Try to parse the sheet
        rows = parse_google_sheets_csv(sheet_id, gid)
        
        if rows:
            print(f"✅ SUCCESS: Found {len(rows)} rows")
            print(f"📋 Headers: {list(rows[0].keys())}")
            
            # Show first few rows
            print(f"\n📄 Sample data (first 3 rows):")
            for i, row in enumerate(rows[:3]):
                print(f"  Row {i+1}: {dict(row)}")
            
            # Check for expected fields
            headers = list(rows[0].keys())
            expected_fields = ['SOW #', 'Deliverable', 'Responsible party', 'DeliverableID', 'Link']
            found_fields = [field for field in expected_fields if any(field.lower() in h.lower() for h in headers)]
            
            print(f"\n🔍 Field Analysis:")
            print(f"  Expected fields: {expected_fields}")
            print(f"  Found fields: {found_fields}")
            print(f"  Missing fields: {set(expected_fields) - set(found_fields)}")
            
            return True
        else:
            print("❌ ERROR: No data rows found")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Main test function."""
    print("Google Sheets Document Index Parser Test")
    print("=" * 50)
    
    # Test URLs
    test_urls = [
        "https://docs.google.com/spreadsheets/d/1YXBh6LHITAPmmwNinWVgYMJhJhqVwOPQj3T0h2PI-UU/edit?usp=sharing",
        "https://docs.google.com/spreadsheets/d/1YXBh6LHITAPmmwNinWVgYMJhJhqVwOPQj3T0h2PI-UU/edit#gid=0"
    ]
    
    success_count = 0
    for url in test_urls:
        if test_sheets_url(url):
            success_count += 1
    
    print(f"\n=== Test Summary ===")
    print(f"Total URLs tested: {len(test_urls)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(test_urls) - success_count}")
    
    if success_count == len(test_urls):
        print("🎉 All tests passed! Google Sheets parsing is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()
