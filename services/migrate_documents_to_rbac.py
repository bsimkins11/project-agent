#!/usr/bin/env python3
"""Migration script to assign existing documents to default client and project."""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from google.cloud import firestore
from packages.shared.config import settings

# Initialize Firestore
db = firestore.Client(project=settings.gcp_project)

# Default tenant IDs
DEFAULT_CLIENT_ID = "client-transparent-partners"
DEFAULT_PROJECT_ID = "project-chr-martech"

def migrate_documents():
    """Migrate all existing documents to default client and project."""
    print("\n" + "="*60)
    print("🔄 MIGRATING DOCUMENTS TO RBAC STRUCTURE")
    print("="*60 + "\n")
    
    # Get all documents
    docs_ref = db.collection("documents")
    all_docs = list(docs_ref.stream())
    
    total_docs = len(all_docs)
    print(f"Found {total_docs} documents to migrate\n")
    
    migrated = 0
    skipped = 0
    errors = 0
    
    for doc in all_docs:
        doc_id = doc.id
        doc_data = doc.to_dict()
        
        try:
            # Check if already migrated
            if doc_data.get("client_id") and doc_data.get("project_id"):
                print(f"⏭️  Skipped {doc_id} - already has client_id and project_id")
                skipped += 1
                continue
            
            # Add multi-tenant fields
            updates = {
                "client_id": DEFAULT_CLIENT_ID,
                "project_id": DEFAULT_PROJECT_ID,
                "visibility": "project",
                "updated_at": datetime.now()
            }
            
            # Update document
            doc.reference.update(updates)
            
            title = doc_data.get("title", "Untitled")[:40]
            print(f"✅ Migrated: {doc_id} - {title}")
            migrated += 1
            
        except Exception as e:
            print(f"❌ ERROR migrating {doc_id}: {e}")
            errors += 1
    
    # Update project document count
    try:
        project_ref = db.collection("projects").document(DEFAULT_PROJECT_ID)
        project_ref.update({"document_count": migrated})
        print(f"\n✅ Updated project document count: {migrated}")
    except Exception as e:
        print(f"\n⚠️  Could not update project count: {e}")
    
    print("\n" + "="*60)
    print("📊 MIGRATION SUMMARY")
    print("="*60)
    print(f"Total documents: {total_docs}")
    print(f"✅ Migrated: {migrated}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"❌ Errors: {errors}")
    print("="*60 + "\n")
    
    if errors > 0:
        print("⚠️  Some documents failed to migrate. Please review errors above.")
        return False
    else:
        print("🎉 All documents successfully migrated!")
        return True

def verify_migration():
    """Verify migration was successful."""
    print("\n" + "="*60)
    print("🔍 VERIFYING MIGRATION")
    print("="*60 + "\n")
    
    # Count documents with client_id and project_id
    docs_ref = db.collection("documents")
    all_docs = list(docs_ref.stream())
    
    with_tenant = 0
    without_tenant = 0
    
    for doc in all_docs:
        doc_data = doc.to_dict()
        if doc_data.get("client_id") and doc_data.get("project_id"):
            with_tenant += 1
        else:
            without_tenant += 1
    
    print(f"Documents with tenant fields: {with_tenant}")
    print(f"Documents without tenant fields: {without_tenant}")
    
    if without_tenant == 0:
        print("\n✅ VERIFICATION PASSED - All documents migrated!")
        return True
    else:
        print(f"\n⚠️  VERIFICATION FAILED - {without_tenant} documents not migrated")
        return False

def main():
    """Main migration function."""
    try:
        # Run migration
        success = migrate_documents()
        
        if not success:
            print("\n❌ Migration failed!")
            return False
        
        # Verify migration
        verified = verify_migration()
        
        if verified:
            print("\n" + "="*60)
            print("🎉 MIGRATION COMPLETE AND VERIFIED!")
            print("="*60)
            print(f"\nAll documents now belong to:")
            print(f"  Client: {DEFAULT_CLIENT_ID}")
            print(f"  Project: {DEFAULT_PROJECT_ID}")
            print(f"\n✅ System ready for multi-tenant RBAC!")
            print("="*60 + "\n")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"\n❌ MIGRATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

