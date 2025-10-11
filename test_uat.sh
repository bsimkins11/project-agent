#!/bin/bash

# Project Agent UAT Testing Script
# This script tests the deployed system in the UAT environment

set -e

# Configuration
PROJECT_ID="transparent-agent-test"
REGION="us-central1"

echo "🧪 Starting Project Agent UAT Testing..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Service URLs
WEB_PORTAL="https://project-agent-web-$PROJECT_ID.a.run.app"
CHAT_API="https://project-agent-chat-api-$PROJECT_ID.a.run.app"
UPLOAD_API="https://project-agent-upload-api-$PROJECT_ID.a.run.app"
INVENTORY_API="https://project-agent-inventory-api-$PROJECT_ID.a.run.app"
DOCUMENTS_API="https://project-agent-documents-api-$PROJECT_ID.a.run.app"
ADMIN_API="https://project-agent-admin-api-$PROJECT_ID.a.run.app"

echo ""
echo "🔍 Testing service health..."

# Test function
test_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo "  Testing $service_name..."
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url/health" || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo "    ✅ $service_name is healthy (HTTP $response)"
        return 0
    else
        echo "    ❌ $service_name is unhealthy (HTTP $response)"
        return 1
    fi
}

# Test all services
test_service "Web Portal" "$WEB_PORTAL"
test_service "Chat API" "$CHAT_API"
test_service "Upload API" "$UPLOAD_API"
test_service "Inventory API" "$INVENTORY_API"
test_service "Documents API" "$DOCUMENTS_API"
test_service "Admin API" "$ADMIN_API"

echo ""
echo "📊 Testing document ingestion..."

# Create a test document
TEST_DOC="test_documents/uat_test.txt"
mkdir -p test_documents
cat > "$TEST_DOC" << EOF
Project Agent UAT Test Document

This is a test document for User Acceptance Testing of the Project Agent system.

Key Features:
- Document upload and processing
- Vector search and retrieval
- Chat interface with citations
- Admin panel for document management

Test Scenarios:
1. Upload this document via the web interface
2. Search for "UAT Test Document" in the chat
3. Verify the document appears in the inventory
4. Test the admin panel functionality

Expected Results:
- Document should be processed successfully
- Search should return relevant results
- Citations should be accurate
- Admin panel should show the document

Test Date: $(date)
Test Environment: UAT
EOF

echo "  Created test document: $TEST_DOC"

# Test document upload via API
echo "  Testing document upload..."
upload_response=$(curl -s -X POST "$UPLOAD_API/upload" \
    -F "file=@$TEST_DOC" \
    -H "Content-Type: multipart/form-data")

if echo "$upload_response" | grep -q '"success":true'; then
    echo "    ✅ Document upload successful"
    doc_id=$(echo "$upload_response" | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)
    echo "    Document ID: $doc_id"
else
    echo "    ❌ Document upload failed"
    echo "    Response: $upload_response"
fi

echo ""
echo "🔍 Testing document search..."

# Test chat API
chat_response=$(curl -s -X POST "$CHAT_API/chat" \
    -H "Content-Type: application/json" \
    -d '{"query": "What is the Project Agent UAT Test Document about?", "filters": {}}')

if echo "$chat_response" | grep -q '"response"'; then
    echo "    ✅ Chat API responding"
    echo "    Response preview: $(echo "$chat_response" | grep -o '"response":"[^"]*"' | head -1)"
else
    echo "    ❌ Chat API not responding correctly"
    echo "    Response: $chat_response"
fi

echo ""
echo "📋 Testing document inventory..."

# Test inventory API
inventory_response=$(curl -s "$INVENTORY_API/documents")

if echo "$inventory_response" | grep -q '"documents"'; then
    echo "    ✅ Inventory API responding"
    doc_count=$(echo "$inventory_response" | grep -o '"total":[0-9]*' | cut -d':' -f2)
    echo "    Total documents: $doc_count"
else
    echo "    ❌ Inventory API not responding correctly"
    echo "    Response: $inventory_response"
fi

echo ""
echo "🌐 Testing web portal..."

# Test web portal accessibility
portal_response=$(curl -s -o /dev/null -w "%{http_code}" "$WEB_PORTAL")

if [ "$portal_response" = "200" ]; then
    echo "    ✅ Web portal accessible"
    echo "    URL: $WEB_PORTAL"
else
    echo "    ❌ Web portal not accessible (HTTP $portal_response)"
fi

echo ""
echo "📊 UAT Test Summary:"
echo "  Web Portal: $WEB_PORTAL"
echo "  Chat API: $CHAT_API"
echo "  Upload API: $UPLOAD_API"
echo "  Inventory API: $INVENTORY_API"
echo "  Documents API: $DOCUMENTS_API"
echo "  Admin API: $ADMIN_API"
echo ""
echo "🧪 Manual Testing Steps:"
echo "  1. Open the web portal in your browser"
echo "  2. Upload the test document: $TEST_DOC"
echo "  3. Try searching for 'UAT Test Document' in the chat"
echo "  4. Check the document inventory"
echo "  5. Test the admin panel"
echo ""
echo "📝 Test Document Location: $TEST_DOC"
echo "✅ UAT testing completed!"


