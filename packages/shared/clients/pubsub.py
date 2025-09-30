"""Pub/Sub client for Project Agent."""

import os
import json
import uuid
from typing import Dict, Any
from google.cloud import pubsub_v1


class PubSubClient:
    """Client for Pub/Sub operations."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.topic_name = os.getenv("PUBSUB_TOPIC_INGESTION", "project-agent-ingestion")
        self.subscription_name = os.getenv("PUBSUB_SUBSCRIPTION_INGESTION", "project-agent-ingestion-sub")
    
    async def publish_ingestion_job(self, job_data: Dict[str, Any]) -> str:
        """Publish ingestion job to Pub/Sub."""
        job_id = str(uuid.uuid4())
        job_data["job_id"] = job_id
        
        topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
        
        message_data = json.dumps(job_data).encode('utf-8')
        future = self.publisher.publish(topic_path, message_data)
        future.result()  # Wait for publish to complete
        
        return job_id
    
    async def pull_messages(self, max_messages: int = 10):
        """Pull messages from Pub/Sub subscription."""
        subscription_path = self.subscriber.subscription_path(
            self.project_id, self.subscription_name
        )
        
        messages = []
        response = self.subscriber.pull(
            request={"subscription": subscription_path, "max_messages": max_messages}
        )
        
        for received_message in response.received_messages:
            try:
                data = json.loads(received_message.message.data.decode('utf-8'))
                messages.append(received_message)
            except json.JSONDecodeError:
                # Skip invalid messages
                continue
        
        return messages
