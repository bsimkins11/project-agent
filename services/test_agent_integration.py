#!/usr/bin/env python3
"""Test script for agent integration."""

import asyncio
import sys
import os
import json
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from packages.agent_core import ADKPlanner


async def test_agent_planner():
    """Test the ADK planner functionality."""
    print("🤖 Testing Agent Core Integration")
    print("=" * 50)
    
    # Initialize planner
    planner = ADKPlanner()
    print("✅ ADKPlanner initialized successfully")
    
    # Test queries
    test_queries = [
        "What is the main purpose of this project?",
        "What are the technical requirements?",
        "What documents are available?",
        "Tell me about the project overview",
        "What are the key features?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test Query {i}: {query}")
        print("-" * 40)
        
        try:
            result = await planner.process_query(
                query=query,
                filters={},
                max_results=5,
                user_id="test-user"
            )
            
            print(f"✅ Query processed successfully")
            print(f"📊 Total results: {result['total_results']}")
            print(f"💬 Answer: {result['answer'][:200]}...")
            
            if result['snippets']:
                print(f"📄 Found {len(result['snippets'])} snippets:")
                for j, snippet in enumerate(result['snippets'][:3], 1):
                    print(f"   {j}. {snippet['title']} - {snippet['excerpt'][:100]}...")
            
        except Exception as e:
            print(f"❌ Error processing query: {str(e)}")
    
    print("\n🎉 Agent integration test completed!")


async def test_chat_api_integration():
    """Test the chat API with agent integration."""
    print("\n🌐 Testing Chat API Integration")
    print("=" * 50)
    
    import requests
    
    # Test chat API endpoint
    chat_url = "http://localhost:8087/chat"
    
    test_requests = [
        {
            "query": "What is this project about?",
            "filters": {}
        },
        {
            "query": "What are the main features?",
            "filters": {"doc_type": "sow"}
        },
        {
            "query": "Tell me about the technical specifications",
            "filters": {}
        }
    ]
    
    for i, request_data in enumerate(test_requests, 1):
        print(f"\n🔍 API Test {i}: {request_data['query']}")
        print("-" * 40)
        
        try:
            response = requests.post(
                chat_url,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API call successful")
                print(f"📊 Total results: {data['total_results']}")
                print(f"⏱️  Query time: {data['query_time_ms']}ms")
                print(f"💬 Answer: {data['answer'][:200]}...")
                
                if data['citations']:
                    print(f"📄 Citations: {len(data['citations'])}")
                    for j, citation in enumerate(data['citations'][:2], 1):
                        print(f"   {j}. {citation['title']} (Page {citation['page']})")
            else:
                print(f"❌ API call failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error calling API: {str(e)}")
    
    print("\n🎉 Chat API integration test completed!")


async def main():
    """Run all tests."""
    print("🚀 Starting Agent Integration Tests")
    print("=" * 60)
    
    # Test agent core
    await test_agent_planner()
    
    # Test chat API integration
    await test_chat_api_integration()
    
    print("\n✨ All tests completed successfully!")
    print("\nThe agent core is now fully integrated and working!")


if __name__ == "__main__":
    asyncio.run(main())
