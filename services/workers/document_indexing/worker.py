"""Document indexing worker for Project Agent."""

import os
import sys
import uuid
import asyncio
from typing import Dict, Any, List
from google.cloud import pubsub_v1
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from packages.shared.clients.gcs import GCSClient
from packages.shared.clients.documentai import DocumentAIClient
from packages.shared.clients.firestore import FirestoreClient
from packages.shared.clients.vector_search import VectorSearchClient
from packages.shared.schemas.document import DocumentMetadata

class DocumentIndexingWorker:
    """Worker for processing and indexing documents."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.subscription_name = os.getenv("INDEXING_SUBSCRIPTION", f"projects/{self.project_id}/subscriptions/document-indexing")
        
        # Initialize clients
        self.gcs_client = GCSClient()
        self.docai_client = DocumentAIClient()
        self.firestore_client = FirestoreClient()
        self.vector_client = VectorSearchClient()
        
        # Initialize Pub/Sub subscriber
        self.subscriber = pubsub_v1.SubscriberClient()
    
    async def process_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Process a document: extract text, create chunks, generate embeddings, and index.
        
        Args:
            doc_id: Document ID to process
            
        Returns:
            Processing results
        """
        try:
            print(f"🔄 Processing document: {doc_id}")
            
            # 1. Get document metadata from Firestore
            doc_metadata = await self.firestore_client.get_document(doc_id)
            if not doc_metadata:
                raise ValueError(f"Document {doc_id} not found in Firestore")
            
            print(f"📄 Document: {doc_metadata.title}")
            
            # Check if document is approved for processing
            if doc_metadata.status != "approved":
                print(f"⏸️  Document {doc_id} is not approved for processing (status: {doc_metadata.status})")
                return {
                    "success": False,
                    "doc_id": doc_id,
                    "error": f"Document not approved for processing (status: {doc_metadata.status})"
                }
            
            # 2. Download document from GCS
            file_content = await self.gcs_client.download_file(doc_metadata.uri)
            print(f"📥 Downloaded {len(file_content)} bytes from GCS")
            
            # 3. Process with Document AI
            processing_result = self.docai_client.process_document(
                file_content=file_content,
                mime_type=self._get_mime_type(doc_metadata.type)
            )
            
            print(f"🤖 Document AI processing completed")
            print(f"   Text length: {len(processing_result['text'])} characters")
            print(f"   Pages: {processing_result['page_count']}")
            print(f"   Confidence: {processing_result['confidence']:.2f}")
            
            # 4. Chunk the text
            text_chunks = self.vector_client.chunk_text(
                processing_result['text'],
                chunk_size=500,
                overlap=50
            )
            
            print(f"✂️  Created {len(text_chunks)} text chunks")
            
            # 5. Generate embeddings and upsert to vector search
            vector_ids = []
            for i, chunk in enumerate(text_chunks):
                # Generate embedding
                embedding = self.vector_client.generate_embedding(chunk)
                
                # Create vector ID
                vector_id = f"{doc_id}_chunk_{i}"
                
                # Prepare metadata
                metadata = {
                    "doc_id": doc_id,
                    "chunk_id": vector_id,
                    "chunk_index": i,
                    "text": chunk,
                    "title": doc_metadata.title,
                    "type": doc_metadata.type,
                    "page": min(i + 1, processing_result['page_count'])  # Approximate page
                }
                
                # Upsert to vector search
                success = await self.vector_client.upsert_vector(vector_id, embedding, metadata)
                if success:
                    vector_ids.append(vector_id)
                
                print(f"📤 Indexed chunk {i+1}/{len(text_chunks)}: {vector_id}")
            
            # 6. Update document metadata with processing results
            doc_metadata.processing_result = processing_result
            doc_metadata.status = "indexed"
            
            # Add vector IDs to metadata (store in a custom field)
            if not hasattr(doc_metadata, 'vector_ids'):
                doc_metadata.__dict__['vector_ids'] = vector_ids
            
            await self.firestore_client.save_document(doc_metadata)
            
            print(f"✅ Document indexing completed successfully")
            print(f"   Vector IDs: {len(vector_ids)}")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "chunks_processed": len(text_chunks),
                "vectors_created": len(vector_ids),
                "processing_result": processing_result
            }
            
        except Exception as e:
            print(f"❌ Document indexing failed: {e}")
            
            # Update document status to failed
            try:
                doc_metadata = await self.firestore_client.get_document(doc_id)
                if doc_metadata:
                    doc_metadata.status = "failed"
                    await self.firestore_client.save_document(doc_metadata)
            except:
                pass
            
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e)
            }
    
    def _get_mime_type(self, doc_type: str) -> str:
        """Convert document type to MIME type."""
        mime_types = {
            "PDF": "application/pdf",
            "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "TXT": "text/plain",
            "MD": "text/markdown",
            "HTML": "text/html"
        }
        return mime_types.get(doc_type, "application/octet-stream")
    
    async def handle_message(self, message):
        """Handle incoming Pub/Sub message."""
        try:
            # Parse message data
            data = message.data.decode('utf-8')
            print(f"📨 Received message: {data}")
            
            # Extract document ID from message
            doc_id = data.strip()
            
            # Process the document
            result = await self.process_document(doc_id)
            
            # Acknowledge the message
            message.ack()
            
            print(f"✅ Message processed successfully: {result}")
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            message.nack()
    
    async def start_worker(self):
        """Start the document indexing worker."""
        print(f"🚀 Starting document indexing worker...")
        print(f"📡 Listening to subscription: {self.subscription_name}")
        
        try:
            # Start pulling messages
            streaming_pull_future = self.subscriber.pull(
                request={"subscription": self.subscription_name, "max_messages": 10},
                callback=self.handle_message
            )
            
            print(f"✅ Worker started successfully")
            
            # Keep the worker running
            await streaming_pull_future
            
        except Exception as e:
            print(f"❌ Worker failed: {e}")
            raise

async def main():
    """Main function to run the worker."""
    worker = DocumentIndexingWorker()
    await worker.start_worker()

if __name__ == "__main__":
    asyncio.run(main())
