"""
Phase 5 Functional Tests - RBAC Validation

Tests all user roles and their permissions across all APIs.
"""

import asyncio
import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from packages.shared.clients.rbac import RBACClient
from packages.shared.clients.auth import get_user_context, check_document_access, filter_documents_by_access
from packages.shared.schemas.rbac import UserRole, PermissionType, get_role_permissions

# Test configuration
TEST_USERS = {
    "superadmin": "superadmin@transparent.partners",
    "account_admin_a": "accountadmin-a@testa.example.com",
    "account_admin_b": "accountadmin-b@testb.example.com",
    "project_admin_1": "projectadmin-1@testa.example.com",
    "project_admin_3": "projectadmin-3@testb.example.com",
    "end_user_12": "enduser-12@testa.example.com",
    "end_user_3": "enduser-3@testb.example.com"
}

class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        if self.failed > 0:
            print("\nFailed Tests:")
            for test in self.tests:
                if not test["passed"]:
                    print(f"  ❌ {test['name']}: {test['message']}")
        print("=" * 60)


async def test_user_context_loading(results: TestResults):
    """Test that user contexts load correctly."""
    print("\n📋 Testing User Context Loading...")
    
    for role_name, email in TEST_USERS.items():
        try:
            context = await get_user_context(email)
            
            # Verify basic context structure
            assert context.get("email") == email, f"Email mismatch for {role_name}"
            assert "role" in context, f"Role missing for {role_name}"
            assert "permissions" in context, f"Permissions missing for {role_name}"
            assert "client_ids" in context, f"Client IDs missing for {role_name}"
            assert "project_ids" in context, f"Project IDs missing for {role_name}"
            
            results.add_result(f"Context loading: {role_name}", True)
            print(f"  ✅ {role_name}: {context['role']}")
            
        except Exception as e:
            results.add_result(f"Context loading: {role_name}", False, str(e))
            print(f"  ❌ {role_name}: {str(e)}")


async def test_role_permissions(results: TestResults):
    """Test that each role has the correct permissions."""
    print("\n🔐 Testing Role Permissions...")
    
    # Expected permissions per role
    expected_permissions = {
        UserRole.SUPER_ADMIN: [
            PermissionType.SYSTEM_CONFIG,
            PermissionType.MANAGE_CLIENTS,
            PermissionType.MANAGE_PROJECTS,
            PermissionType.MANAGE_ALL_USERS
        ],
        UserRole.ACCOUNT_ADMIN: [
            PermissionType.VIEW_CLIENTS,
            PermissionType.MANAGE_PROJECTS,
            PermissionType.MANAGE_CLIENT_USERS
        ],
        UserRole.PROJECT_ADMIN: [
            PermissionType.UPLOAD_DOCUMENTS,
            PermissionType.APPROVE_DOCUMENTS,
            PermissionType.DELETE_DOCUMENTS
        ],
        UserRole.END_USER: [
            PermissionType.VIEW_DOCUMENTS,
            PermissionType.USE_CHAT
        ]
    }
    
    for role, expected_perms in expected_permissions.items():
        actual_perms = get_role_permissions(role)
        
        for perm in expected_perms:
            if perm in actual_perms:
                results.add_result(f"Permission {perm.value} in {role.value}", True)
                print(f"  ✅ {role.value} has {perm.value}")
            else:
                results.add_result(f"Permission {perm.value} in {role.value}", False, "Permission missing")
                print(f"  ❌ {role.value} missing {perm.value}")


async def test_super_admin_access(results: TestResults):
    """Test Super Admin has unrestricted access."""
    print("\n👑 Testing Super Admin Access...")
    
    email = TEST_USERS["superadmin"]
    context = await get_user_context(email)
    
    # Super admin should have access to everything
    tests = [
        ("Role is SUPER_ADMIN", context["role"] == UserRole.SUPER_ADMIN),
        ("Has SYSTEM_CONFIG permission", PermissionType.SYSTEM_CONFIG in context["permissions"]),
        ("Has MANAGE_CLIENTS permission", PermissionType.MANAGE_CLIENTS in context["permissions"]),
        ("Has MANAGE_ALL_USERS permission", PermissionType.MANAGE_ALL_USERS in context["permissions"])
    ]
    
    for test_name, passed in tests:
        results.add_result(f"Super Admin: {test_name}", passed)
        print(f"  {'✅' if passed else '❌'} {test_name}")


async def test_account_admin_boundaries(results: TestResults):
    """Test Account Admin client boundaries."""
    print("\n🏢 Testing Account Admin Client Boundaries...")
    
    # Test Account Admin A (Client A)
    context_a = await get_user_context(TEST_USERS["account_admin_a"])
    
    tests_a = [
        ("Has access to Client A", "client-test-a" in context_a["client_ids"]),
        ("NO access to Client B", "client-test-b" not in context_a["client_ids"]),
        ("Has access to Project 1", "project-test-1" in context_a["project_ids"]),
        ("Has access to Project 2", "project-test-2" in context_a["project_ids"]),
        ("NO access to Project 3", "project-test-3" not in context_a["project_ids"]),
        ("NO access to Project 4", "project-test-4" not in context_a["project_ids"])
    ]
    
    for test_name, passed in tests_a:
        results.add_result(f"Account Admin A: {test_name}", passed)
        print(f"  {'✅' if passed else '❌'} Account Admin A: {test_name}")
    
    # Test Account Admin B (Client B)
    context_b = await get_user_context(TEST_USERS["account_admin_b"])
    
    tests_b = [
        ("Has access to Client B", "client-test-b" in context_b["client_ids"]),
        ("NO access to Client A", "client-test-a" not in context_b["client_ids"]),
        ("Has access to Project 3", "project-test-3" in context_b["project_ids"]),
        ("Has access to Project 4", "project-test-4" in context_b["project_ids"]),
        ("NO access to Project 1", "project-test-1" not in context_b["project_ids"]),
        ("NO access to Project 2", "project-test-2" not in context_b["project_ids"])
    ]
    
    for test_name, passed in tests_b:
        results.add_result(f"Account Admin B: {test_name}", passed)
        print(f"  {'✅' if passed else '❌'} Account Admin B: {test_name}")


async def test_project_admin_boundaries(results: TestResults):
    """Test Project Admin project boundaries."""
    print("\n📁 Testing Project Admin Project Boundaries...")
    
    # Test Project Admin 1 (Project 1 only)
    context_1 = await get_user_context(TEST_USERS["project_admin_1"])
    
    tests_1 = [
        ("Has access to Project 1", "project-test-1" in context_1["project_ids"]),
        ("NO access to Project 2", "project-test-2" not in context_1["project_ids"]),
        ("NO access to Project 3", "project-test-3" not in context_1["project_ids"]),
        ("Has UPLOAD_DOCUMENTS", PermissionType.UPLOAD_DOCUMENTS in context_1["permissions"]),
        ("Has APPROVE_DOCUMENTS", PermissionType.APPROVE_DOCUMENTS in context_1["permissions"]),
        ("NO MANAGE_CLIENTS", PermissionType.MANAGE_CLIENTS not in context_1["permissions"])
    ]
    
    for test_name, passed in tests_1:
        results.add_result(f"Project Admin 1: {test_name}", passed)
        print(f"  {'✅' if passed else '❌'} Project Admin 1: {test_name}")


async def test_end_user_restrictions(results: TestResults):
    """Test End User restrictions."""
    print("\n👤 Testing End User Restrictions...")
    
    # Test End User with Projects 1-2
    context_12 = await get_user_context(TEST_USERS["end_user_12"])
    
    tests_12 = [
        ("Has access to Project 1", "project-test-1" in context_12["project_ids"]),
        ("Has access to Project 2", "project-test-2" in context_12["project_ids"]),
        ("NO access to Project 3", "project-test-3" not in context_12["project_ids"]),
        ("Has VIEW_DOCUMENTS", PermissionType.VIEW_DOCUMENTS in context_12["permissions"]),
        ("Has USE_CHAT", PermissionType.USE_CHAT in context_12["permissions"]),
        ("NO UPLOAD_DOCUMENTS", PermissionType.UPLOAD_DOCUMENTS not in context_12["permissions"]),
        ("NO MANAGE_CLIENTS", PermissionType.MANAGE_CLIENTS not in context_12["permissions"]),
        ("NO MANAGE_PROJECTS", PermissionType.MANAGE_PROJECTS not in context_12["permissions"])
    ]
    
    for test_name, passed in tests_12:
        results.add_result(f"End User 1-2: {test_name}", passed)
        print(f"  {'✅' if passed else '❌'} End User 1-2: {test_name}")


async def test_document_filtering(results: TestResults):
    """Test document filtering by user access."""
    print("\n📄 Testing Document Filtering...")
    
    # Create mock documents
    mock_documents = [
        {"id": "doc1", "title": "Doc 1", "project_id": "project-test-1", "client_id": "client-test-a"},
        {"id": "doc2", "title": "Doc 2", "project_id": "project-test-2", "client_id": "client-test-a"},
        {"id": "doc3", "title": "Doc 3", "project_id": "project-test-3", "client_id": "client-test-b"},
        {"id": "doc4", "title": "Doc 4", "project_id": "project-test-4", "client_id": "client-test-b"},
    ]
    
    # Test Project Admin 1 (should see only Project 1 docs)
    filtered_1 = await filter_documents_by_access(TEST_USERS["project_admin_1"], mock_documents)
    tests = [
        ("Project Admin 1 sees 1 document", len(filtered_1) == 1),
        ("Project Admin 1 sees only doc1", len(filtered_1) == 1 and filtered_1[0]["id"] == "doc1" if filtered_1 else False)
    ]
    
    for test_name, passed in tests:
        results.add_result(f"Document filtering: {test_name}", passed)
        print(f"  {'✅' if passed else '❌'} {test_name}")
    
    # Test End User 1-2 (should see Projects 1-2 docs)
    filtered_12 = await filter_documents_by_access(TEST_USERS["end_user_12"], mock_documents)
    tests = [
        ("End User 1-2 sees 2 documents", len(filtered_12) == 2),
        ("End User 1-2 sees doc1 and doc2", len(filtered_12) == 2 and 
         any(d["id"] == "doc1" for d in filtered_12) and 
         any(d["id"] == "doc2" for d in filtered_12) if filtered_12 else False)
    ]
    
    for test_name, passed in tests:
        results.add_result(f"Document filtering: {test_name}", passed)
        print(f"  {'✅' if passed else '❌'} {test_name}")
    
    # Test Super Admin (should see all docs)
    filtered_super = await filter_documents_by_access(TEST_USERS["superadmin"], mock_documents)
    test_passed = len(filtered_super) == 4
    results.add_result("Document filtering: Super Admin sees all 4 documents", test_passed)
    print(f"  {'✅' if test_passed else '❌'} Super Admin sees all 4 documents")


async def run_all_tests():
    """Run all functional tests."""
    results = TestResults()
    
    print("=" * 60)
    print("PHASE 5 FUNCTIONAL TESTS")
    print("=" * 60)
    
    try:
        await test_user_context_loading(results)
        await test_role_permissions(results)
        await test_super_admin_access(results)
        await test_account_admin_boundaries(results)
        await test_project_admin_boundaries(results)
        await test_end_user_restrictions(results)
        await test_document_filtering(results)
        
    except Exception as e:
        print(f"\n❌ Critical error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    
    results.print_summary()
    
    # Return exit code
    return 0 if results.failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

