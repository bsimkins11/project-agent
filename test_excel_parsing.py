#!/usr/bin/env python3
"""
Test script to examine the document structure Excel file using the admin API parsing logic.
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.append('/Users/avpuser/Cursor_Projects/TP_Project_Agent')

from packages.shared.schemas.document import DocumentStatus, DocType, DocumentMetadata

def test_google_sheets_parsing():
    """Test the Google Sheets parsing logic with a sample URL."""
    print("Testing Google Sheets parsing logic...")
    print("=" * 60)
    
    # Test URL from your previous message
    test_url = "https://docs.google.com/spreadsheets/d/1YXBh6LHITAPmmwNinWVgYMJhJhqVwOPQj3T0h2PI-UU/edit?usp=sharing"
    
    # Import the parsing function from the admin API
    try:
        from services.api.admin.app import parse_google_sheets_csv, map_document_from_row
        
        print(f"Testing URL: {test_url}")
        
        # Test the parsing (this will fail without proper access, but we can see the error handling)
        try:
            documents = parse_google_sheets_csv(test_url)
            print(f"Successfully parsed {len(documents)} documents")
            
            for i, doc in enumerate(documents):
                print(f"\nDocument {i+1}:")
                print(f"  Title: {doc.get('title', 'N/A')}")
                print(f"  Source URI: {doc.get('source_uri', 'N/A')}")
                print(f"  Doc Type: {doc.get('doc_type', 'N/A')}")
                print(f"  SOW #: {doc.get('sow_number', 'N/A')}")
                print(f"  Deliverable: {doc.get('deliverable', 'N/A')}")
                print(f"  Responsible Party: {doc.get('responsible_party', 'N/A')}")
                print(f"  Deliverable ID: {doc.get('deliverable_id', 'N/A')}")
                print(f"  Link: {doc.get('link', 'N/A')}")
                print(f"  Notes: {doc.get('notes', 'N/A')}")
                print(f"  Requires Permission: {doc.get('requires_permission', False)}")
                print(f"  Status: {doc.get('status', 'N/A')}")
                
        except Exception as e:
            print(f"Expected error (no access): {e}")
            
    except ImportError as e:
        print(f"Could not import admin functions: {e}")

def test_document_mapping():
    """Test the document mapping logic with sample data."""
    print("\n" + "=" * 60)
    print("Testing Document Mapping Logic")
    print("=" * 60)
    
    # Sample data that might be in your Excel file
    sample_rows = [
        {
            "Title": "Project Overview Document",
            "Link": "https://drive.google.com/file/d/1abc123def456ghi789jkl/view",
            "Type": "sow",
            "SOW #": "SOW-001",
            "Deliverable": "Project Planning",
            "Responsible party": "John Doe",
            "DeliverableID": "DEL-001",
            "Notes": "Initial project documentation"
        },
        {
            "Title": "Technical Specifications",
            "Link": "https://docs.google.com/document/d/2def456ghi789jkl123abc/edit",
            "Type": "deliverable",
            "SOW #": "SOW-001",
            "Deliverable": "Technical Design",
            "Responsible party": "Jane Smith",
            "DeliverableID": "DEL-002",
            "Notes": "Detailed technical requirements"
        },
        {
            "Title": "Timeline Document",
            "Link": "https://drive.google.com/file/d/3ghi789jkl123abc456def/view",
            "Type": "timeline",
            "SOW #": "SOW-002",
            "Deliverable": "Project Schedule",
            "Responsible party": "Mike Johnson",
            "DeliverableID": "DEL-003",
            "Notes": "Project timeline and milestones"
        }
    ]
    
    try:
        from services.api.admin.app import map_document_from_row
        
        for i, row in enumerate(sample_rows):
            print(f"\n--- Sample Row {i+1} ---")
            print(f"Input: {row}")
            
            try:
                doc_data = map_document_from_row(row)
                print(f"Mapped Document:")
                print(f"  ID: {doc_data.get('id', 'N/A')}")
                print(f"  Title: {doc_data.get('title', 'N/A')}")
                print(f"  Source URI: {doc_data.get('source_uri', 'N/A')}")
                print(f"  Doc Type: {doc_data.get('doc_type', 'N/A')}")
                print(f"  SOW #: {doc_data.get('sow_number', 'N/A')}")
                print(f"  Deliverable: {doc_data.get('deliverable', 'N/A')}")
                print(f"  Responsible Party: {doc_data.get('responsible_party', 'N/A')}")
                print(f"  Deliverable ID: {doc_data.get('deliverable_id', 'N/A')}")
                print(f"  Link: {doc_data.get('link', 'N/A')}")
                print(f"  Notes: {doc_data.get('notes', 'N/A')}")
                print(f"  Requires Permission: {doc_data.get('requires_permission', False)}")
                print(f"  Status: {doc_data.get('status', 'N/A')}")
                print(f"  Drive File ID: {doc_data.get('drive_file_id', 'N/A')}")
                print(f"  Drive File Type: {doc_data.get('drive_file_type', 'N/A')}")
                
            except Exception as e:
                print(f"Error mapping row: {e}")
                
    except ImportError as e:
        print(f"Could not import mapping function: {e}")

def main():
    print("Testing Document Index Parsing and Mapping")
    print("=" * 60)
    
    # Test the Google Sheets parsing
    test_google_sheets_parsing()
    
    # Test the document mapping
    test_document_mapping()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("Note: The confidence field has been removed from the parsing logic.")
    print("The system now maps documents without the confidence variable.")

if __name__ == "__main__":
    main()
