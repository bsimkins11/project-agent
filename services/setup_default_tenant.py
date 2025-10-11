#!/usr/bin/env python3
"""Setup script to create default client and project for existing documents."""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from google.cloud import firestore
from packages.shared.schemas.rbac import Client, Project, UserRole, UserProfile
from packages.shared.config import settings

# Initialize Firestore
db = firestore.Client(project=settings.gcp_project)

def create_default_client():
    """Create the default Transparent Partners client."""
    client = Client(
        id="client-transparent-partners",
        name="Transparent Partners",
        domain="transparent.partners",
        status="active",
        created_by="system@transparent.partners",
        contact_email="admin@transparent.partners",
        contact_name="Admin Team",
        industry="Consulting & Technology",
        notes="Default client for Transparent Partners internal projects"
    )
    
    print(f"Creating default client: {client.name}")
    db.collection("clients").document(client.id).set(client.dict())
    print(f"✅ Client created: {client.id}")
    return client

def create_default_project(client_id: str):
    """Create the default CHR MarTech Enablement project."""
    project = Project(
        id="project-chr-martech",
        client_id=client_id,
        name="CHR MarTech Enablement",
        code="CHR-MT-001",
        status="active",
        created_by="system@transparent.partners",
        start_date=datetime(2024, 11, 21),  # From your kickoff date
        description="CHR MarTech Enablement project with 94 deliverables",
        tags=["martech", "enablement", "chr", "sow1", "sow2", "sow3"],
        document_count=0  # Will be updated after migration
    )
    
    print(f"Creating default project: {project.name}")
    db.collection("projects").document(project.id).set(project.dict())
    print(f"✅ Project created: {project.id}")
    return project

def create_super_admin(client_id: str, project_id: str):
    """Create super admin user."""
    admin = UserProfile(
        id="user-super-admin",
        email="admin@transparent.partners",
        name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        status="active",
        client_ids=[client_id],
        project_ids=[project_id],
        department="Engineering",
        title="System Administrator"
    )
    
    print(f"Creating super admin user: {admin.email}")
    db.collection("users").document(admin.id).set(admin.dict())
    print(f"✅ Super admin created: {admin.id}")
    return admin

def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("🚀 SETTING UP DEFAULT TENANT")
    print("="*60 + "\n")
    
    try:
        # Create default client
        client = create_default_client()
        
        # Create default project
        project = create_default_project(client.id)
        
        # Create super admin
        admin = create_super_admin(client.id, project.id)
        
        print("\n" + "="*60)
        print("✅ DEFAULT TENANT SETUP COMPLETE!")
        print("="*60)
        print(f"\nClient ID: {client.id}")
        print(f"Client Name: {client.name}")
        print(f"\nProject ID: {project.id}")
        print(f"Project Name: {project.name}")
        print(f"\nSuper Admin: {admin.email}")
        print(f"\n🎯 Ready for document migration!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

