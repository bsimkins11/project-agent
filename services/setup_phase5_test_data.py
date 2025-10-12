"""
Setup test data for Phase 5 RBAC testing.

This script creates:
- Test clients (Client A, Client B)
- Test projects (Projects 1-4)
- Test users with different roles
- Assigns users to clients/projects
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from packages.shared.schemas.rbac import (
    Client, Project, UserProfile, UserRole
)
from packages.shared.clients.rbac import RBACClient

# Test data configuration
TEST_DATA = {
    "clients": [
        {
            "id": "client-test-a",
            "name": "Test Client A",
            "domain": "testa.example.com",
            "contact_email": "admin@testa.example.com",
            "contact_name": "Client A Admin",
            "industry": "Technology"
        },
        {
            "id": "client-test-b",
            "name": "Test Client B",
            "domain": "testb.example.com",
            "contact_email": "admin@testb.example.com",
            "contact_name": "Client B Admin",
            "industry": "Finance"
        }
    ],
    "projects": [
        {
            "id": "project-test-1",
            "client_id": "client-test-a",
            "name": "Test Project 1",
            "code": "TEST-P1",
            "description": "Test project for Client A - Project 1"
        },
        {
            "id": "project-test-2",
            "client_id": "client-test-a",
            "name": "Test Project 2",
            "code": "TEST-P2",
            "description": "Test project for Client A - Project 2"
        },
        {
            "id": "project-test-3",
            "client_id": "client-test-b",
            "name": "Test Project 3",
            "code": "TEST-P3",
            "description": "Test project for Client B - Project 3"
        },
        {
            "id": "project-test-4",
            "client_id": "client-test-b",
            "name": "Test Project 4",
            "code": "TEST-P4",
            "description": "Test project for Client B - Project 4"
        }
    ],
    "users": [
        {
            "id": "user-test-superadmin",
            "email": "superadmin@transparent.partners",
            "name": "Test Super Admin",
            "role": UserRole.SUPER_ADMIN,
            "client_ids": [],  # Super admin has access to all
            "project_ids": []  # Super admin has access to all
        },
        {
            "id": "user-test-account-admin-a",
            "email": "accountadmin-a@testa.example.com",
            "name": "Test Account Admin A",
            "role": UserRole.ACCOUNT_ADMIN,
            "client_ids": ["client-test-a"],
            "project_ids": ["project-test-1", "project-test-2"]  # All projects in Client A
        },
        {
            "id": "user-test-account-admin-b",
            "email": "accountadmin-b@testb.example.com",
            "name": "Test Account Admin B",
            "role": UserRole.ACCOUNT_ADMIN,
            "client_ids": ["client-test-b"],
            "project_ids": ["project-test-3", "project-test-4"]  # All projects in Client B
        },
        {
            "id": "user-test-project-admin-1",
            "email": "projectadmin-1@testa.example.com",
            "name": "Test Project Admin 1",
            "role": UserRole.PROJECT_ADMIN,
            "client_ids": ["client-test-a"],
            "project_ids": ["project-test-1"]  # Only Project 1
        },
        {
            "id": "user-test-project-admin-3",
            "email": "projectadmin-3@testb.example.com",
            "name": "Test Project Admin 3",
            "role": UserRole.PROJECT_ADMIN,
            "client_ids": ["client-test-b"],
            "project_ids": ["project-test-3"]  # Only Project 3
        },
        {
            "id": "user-test-enduser-12",
            "email": "enduser-12@testa.example.com",
            "name": "Test End User 1-2",
            "role": UserRole.END_USER,
            "client_ids": ["client-test-a"],
            "project_ids": ["project-test-1", "project-test-2"]  # Projects 1 and 2
        },
        {
            "id": "user-test-enduser-3",
            "email": "enduser-3@testb.example.com",
            "name": "Test End User 3",
            "role": UserRole.END_USER,
            "client_ids": ["client-test-b"],
            "project_ids": ["project-test-3"]  # Only Project 3
        }
    ]
}


async def setup_test_data():
    """Setup all test data."""
    rbac = RBACClient()
    
    print("=" * 60)
    print("PHASE 5 TEST DATA SETUP")
    print("=" * 60)
    print()
    
    # Create clients
    print("📋 Creating test clients...")
    for client_data in TEST_DATA["clients"]:
        try:
            client = Client(
                id=client_data["id"],
                name=client_data["name"],
                domain=client_data["domain"],
                status="active",
                created_by="system@transparent.partners",
                contact_email=client_data["contact_email"],
                contact_name=client_data["contact_name"],
                industry=client_data["industry"]
            )
            await rbac.create_client(client, "system@transparent.partners")
            print(f"  ✅ Created client: {client.name} ({client.id})")
        except Exception as e:
            print(f"  ⚠️  Client {client_data['id']} may already exist: {str(e)}")
    
    print()
    
    # Create projects
    print("📁 Creating test projects...")
    for project_data in TEST_DATA["projects"]:
        try:
            project = Project(
                id=project_data["id"],
                client_id=project_data["client_id"],
                name=project_data["name"],
                code=project_data["code"],
                status="active",
                created_by="system@transparent.partners",
                description=project_data["description"]
            )
            await rbac.create_project(project, "system@transparent.partners")
            print(f"  ✅ Created project: {project.name} ({project.id})")
        except Exception as e:
            print(f"  ⚠️  Project {project_data['id']} may already exist: {str(e)}")
    
    print()
    
    # Create users
    print("👥 Creating test users...")
    for user_data in TEST_DATA["users"]:
        try:
            user = UserProfile(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data["name"],
                role=user_data["role"],
                status="active",
                client_ids=user_data["client_ids"],
                project_ids=user_data["project_ids"]
            )
            await rbac.create_user(user, "system@transparent.partners")
            print(f"  ✅ Created user: {user.name} ({user.role.value}) - {user.email}")
        except Exception as e:
            print(f"  ⚠️  User {user_data['email']} may already exist: {str(e)}")
    
    print()
    print("=" * 60)
    print("✅ TEST DATA SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("Test Users Created:")
    print("-" * 60)
    for user_data in TEST_DATA["users"]:
        print(f"  Role: {user_data['role'].value:20} Email: {user_data['email']}")
        if user_data['project_ids']:
            print(f"    Projects: {', '.join(user_data['project_ids'])}")
    print()
    print("Next Steps:")
    print("  1. Run functional tests: python services/test_phase5_functional.py")
    print("  2. Run security tests: python services/test_phase5_security.py")
    print("  3. Run performance tests: python services/test_phase5_performance.py")
    print()


async def cleanup_test_data():
    """Cleanup test data (optional)."""
    rbac = RBACClient()
    
    print("🧹 Cleaning up test data...")
    
    # Note: In production, you might want to implement soft deletes
    # For now, we'll just print what would be deleted
    
    print("  Test users:")
    for user_data in TEST_DATA["users"]:
        print(f"    - {user_data['email']}")
    
    print("  Test projects:")
    for project_data in TEST_DATA["projects"]:
        print(f"    - {project_data['name']}")
    
    print("  Test clients:")
    for client_data in TEST_DATA["clients"]:
        print(f"    - {client_data['name']}")
    
    print()
    print("⚠️  Note: Actual cleanup requires delete methods to be implemented.")
    print("    For now, test data will remain in Firestore.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Phase 5 test data")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup test data instead of creating")
    args = parser.parse_args()
    
    if args.cleanup:
        asyncio.run(cleanup_test_data())
    else:
        asyncio.run(setup_test_data())

