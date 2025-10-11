#!/usr/bin/env python3
"""
Test script to examine the document structure Excel file and test parsing logic.
"""

import pandas as pd
import sys
import os

# Add the project root to the path
sys.path.append('/Users/avpuser/Cursor_Projects/TP_Project_Agent')

from packages.shared.schemas.document import DocumentStatus, DocType, DocumentMetadata

def examine_excel_structure(file_path):
    """Examine the structure of the Excel file."""
    print(f"Examining file: {file_path}")
    print("=" * 60)
    
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        print(f"File shape: {df.shape} (rows x columns)")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst 5 rows:")
        print(df.head())
        
        print("\nColumn data types:")
        print(df.dtypes)
        
        print("\nSample data from each column:")
        for col in df.columns:
            print(f"\n{col}:")
            print(f"  Sample values: {df[col].dropna().head(3).tolist()}")
            print(f"  Non-null count: {df[col].notna().sum()}")
            print(f"  Null count: {df[col].isna().sum()}")
        
        return df
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def test_document_mapping(df):
    """Test the document mapping logic."""
    print("\n" + "=" * 60)
    print("TESTING DOCUMENT MAPPING")
    print("=" * 60)
    
    if df is None or df.empty:
        print("No data to test")
        return
    
    # Test mapping for each row
    for idx, row in df.iterrows():
        print(f"\n--- Row {idx + 1} ---")
        print(f"Raw data: {row.to_dict()}")
        
        try:
            # Simulate the mapping logic from the admin API
            title = str(row.get('Title', row.get('title', row.get('Document Title', '')))).strip()
            source_uri = str(row.get('Link', row.get('link', row.get('URL', row.get('url', ''))))).strip()
            doc_type_str = str(row.get('Type', row.get('type', row.get('Document Type', 'misc')))).strip().lower()
            sow_number = str(row.get('SOW #', row.get('SOW Number', row.get('sow_number', '')))).strip()
            deliverable = str(row.get('Deliverable', row.get('deliverable', ''))).strip()
            responsible_party = str(row.get('Responsible party', row.get('Responsible Party', row.get('responsible_party', '')))).strip()
            deliverable_id = str(row.get('DeliverableID', row.get('Deliverable ID', row.get('deliverable_id', '')))).strip()
            link = str(row.get('Link', row.get('link', ''))).strip()
            notes = str(row.get('Notes', row.get('notes', ''))).strip()
            
            # Map doc_type
            valid_types = ['sow', 'timeline', 'deliverable', 'misc']
            if doc_type_str not in valid_types:
                doc_type_str = 'misc'
            
            # Check if this is a Google Drive URL
            is_google_drive = 'drive.google.com' in source_uri or 'docs.google.com' in source_uri
            
            print(f"  Mapped values:")
            print(f"    Title: '{title}'")
            print(f"    Source URI: '{source_uri}'")
            print(f"    Doc Type: '{doc_type_str}'")
            print(f"    SOW #: '{sow_number}'")
            print(f"    Deliverable: '{deliverable}'")
            print(f"    Responsible Party: '{responsible_party}'")
            print(f"    Deliverable ID: '{deliverable_id}'")
            print(f"    Link: '{link}'")
            print(f"    Notes: '{notes}'")
            print(f"    Is Google Drive: {is_google_drive}")
            print(f"    Would require permission: {is_google_drive}")
            
            if is_google_drive:
                print(f"    Status: {DocumentStatus.REQUEST_ACCESS.value}")
            else:
                print(f"    Status: {DocumentStatus.UPLOADED.value}")
                
        except Exception as e:
            print(f"  Error mapping row: {e}")

def main():
    file_path = "/Users/avpuser/Cursor_Projects/TP_Project_Agent/test_documents/Checkers_Folder-document structure.xlsx"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    # Examine the Excel structure
    df = examine_excel_structure(file_path)
    
    # Test document mapping
    test_document_mapping(df)

if __name__ == "__main__":
    main()
