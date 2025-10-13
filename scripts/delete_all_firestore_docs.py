#!/usr/bin/env python3
"""
Delete all documents from Firestore - POC Reset Script

Usage:
    python scripts/delete_all_firestore_docs.py
    
This script will:
1. Connect to Firestore
2. List all documents in the 'documents' collection
3. Delete them one by one
4. Show progress and final count
"""

import os
import sys
from google.cloud import firestore
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def delete_all_documents():
    """Delete all documents from Firestore."""
    
    print("=" * 60)
    print("POC RESET: Delete All Documents")
    print("=" * 60)
    print()
    
    # Initialize Firestore
    print("📡 Connecting to Firestore...")
    try:
        db = firestore.Client()
        print("✅ Connected successfully!")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print("\nMake sure you have:")
        print("1. GOOGLE_APPLICATION_CREDENTIALS environment variable set")
        print("2. Or running on GCP with default credentials")
        return
    
    # Get all documents
    print("\n📝 Fetching all documents...")
    try:
        docs_ref = db.collection("documents")
        docs = list(docs_ref.stream())
        total_count = len(docs)
        print(f"✅ Found {total_count} documents")
    except Exception as e:
        print(f"❌ Failed to fetch documents: {e}")
        return
    
    if total_count == 0:
        print("\n✨ No documents to delete. Collection is already empty!")
        return
    
    # Confirm deletion
    print("\n⚠️  WARNING: This will permanently delete all documents!")
    response = input(f"\nAre you sure you want to delete {total_count} documents? (yes/no): ")
    
    if response.lower() != "yes":
        print("\n❌ Deletion cancelled.")
        return
    
    # Delete documents
    print(f"\n🗑️  Deleting {total_count} documents...")
    deleted_count = 0
    failed_count = 0
    
    for i, doc in enumerate(docs, 1):
        try:
            doc_id = doc.id
            doc_data = doc.to_dict()
            title = doc_data.get("title", "Untitled")
            
            # Delete the document
            doc.reference.delete()
            deleted_count += 1
            
            # Show progress every 10 documents
            if i % 10 == 0 or i == total_count:
                print(f"  Progress: {i}/{total_count} ({i*100//total_count}%)")
            
        except Exception as e:
            failed_count += 1
            print(f"  ❌ Failed to delete {doc_id}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("DELETION COMPLETE")
    print("=" * 60)
    print(f"✅ Deleted: {deleted_count} documents")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count} documents")
    print(f"\n🎯 Ready for new document index import!")
    print("=" * 60)


if __name__ == "__main__":
    delete_all_documents()

