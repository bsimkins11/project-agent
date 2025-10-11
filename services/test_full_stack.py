"""Test full stack integration between frontend and backend."""

import requests
import json
import time

def test_full_stack():
    """Test the complete flow from frontend to backend."""
    print("🚀 Testing Full Stack Integration")
    print("=" * 50)
    
    # Test 1: Backend API Health
    print("\n1. Testing Backend API Health...")
    try:
        response = requests.get("http://localhost:8001/health")
        if response.status_code == 200:
            print("✅ Backend API is healthy")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Backend API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend API connection failed: {e}")
        return False
    
    # Test 2: Frontend Accessibility
    print("\n2. Testing Frontend Accessibility...")
    try:
        response = requests.get("http://localhost:3000/")
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            if "Project Agent" in response.text:
                print("✅ Frontend content loaded correctly")
            else:
                print("⚠️  Frontend loaded but content may be incomplete")
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend connection failed: {e}")
        return False
    
    # Test 3: Chat API Integration
    print("\n3. Testing Chat API Integration...")
    try:
        chat_request = {
            "query": "What are the key findings in the project documentation?",
            "filters": {
                "doc_type": "PDF"
            }
        }
        
        response = requests.post(
            "http://localhost:8001/chat",
            headers={"Content-Type": "application/json"},
            data=json.dumps(chat_request)
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat API integration successful")
            print(f"   Query: {chat_request['query']}")
            print(f"   Answer: {data['answer'][:100]}...")
            print(f"   Citations: {len(data['citations'])} found")
            print(f"   Response time: {data['query_time_ms']}ms")
        else:
            print(f"❌ Chat API returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat API integration failed: {e}")
        return False
    
    # Test 4: Inventory API
    print("\n4. Testing Inventory API...")
    try:
        response = requests.get("http://localhost:8001/inventory")
        if response.status_code == 200:
            data = response.json()
            print("✅ Inventory API working")
            print(f"   Documents: {data['total']} total")
            print(f"   Available filters: {len(data['filters']['types'])} types")
        else:
            print(f"❌ Inventory API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Inventory API failed: {e}")
        return False
    
    # Test 5: Document Detail API
    print("\n5. Testing Document Detail API...")
    try:
        response = requests.get("http://localhost:8001/documents/doc-001")
        if response.status_code == 200:
            data = response.json()
            print("✅ Document Detail API working")
            print(f"   Document ID: {data['id']}")
            print(f"   Title: {data['title']}")
            print(f"   Chunks: {len(data['chunks'])} available")
        else:
            print(f"❌ Document Detail API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Document Detail API failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 FULL STACK INTEGRATION TEST PASSED!")
    print("✅ All services are working together correctly")
    print("\nNext steps:")
    print("- Open http://localhost:3000 in your browser")
    print("- Try asking questions in the chat interface")
    print("- Test the document filters")
    print("- Upload documents through the admin interface")
    
    return True

if __name__ == "__main__":
    test_full_stack()
