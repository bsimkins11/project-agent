"""Create Document AI processor using REST API."""

import requests
import json
import os
from google.auth import default
from google.auth.transport.requests import Request

def create_documentai_processor():
    """Create a Document AI processor for project documents."""
    
    # Get credentials
    credentials, project_id = default()
    credentials.refresh(Request())
    
    # Document AI API endpoint
    url = f"https://documentai.googleapis.com/v1/projects/{project_id}/locations/us/processors"
    
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }
    
    # Processor configuration
    processor_data = {
        "displayName": "project-agent-processor",
        "type": "FORM_PARSER_PROCESSOR"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(processor_data))
        
        if response.status_code == 200:
            result = response.json()
            processor_name = result.get('name')
            print(f"✅ Document AI processor created successfully!")
            print(f"   Processor Name: {processor_name}")
            print(f"   Display Name: {result.get('displayName')}")
            print(f"   Type: {result.get('type')}")
            
            # Extract processor ID for environment variable
            processor_id = processor_name.split('/')[-1]
            print(f"\n🔧 Add this to your .env file:")
            print(f"   DOC_AI_PROCESSOR=projects/{project_id}/locations/us/processors/{processor_id}")
            
            return processor_name
        else:
            print(f"❌ Failed to create processor: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating processor: {e}")
        return None

if __name__ == "__main__":
    create_documentai_processor()
