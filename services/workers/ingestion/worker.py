"""Document ingestion worker for Project Agent."""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

from packages.shared.clients.pubsub import PubSubClient
from packages.shared.clients.firestore import FirestoreClient
from packages.shared.clients.gcs import GCSClient
from packages.shared.clients.documentai import DocumentAIClient
from packages.shared.clients.vision import VisionClient
from packages.shared.clients.vector_search import VectorSearchClient
from packages.shared.clients.drive import DriveClient
from packages.shared.schemas import DocumentMetadata, DocumentStatus, MediaType, DocType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
pubsub = PubSubClient()
firestore = FirestoreClient()
gcs = GCSClient()
docai = DocumentAIClient()
vision = VisionClient()
vector_search = VectorSearchClient()
drive = DriveClient()


class IngestionWorker:
    """Main ingestion worker class."""
    
    def __init__(self):
        self.running = False
    
    async def start(self):
        """Start the worker."""
        logger.info("Starting ingestion worker...")
        self.running = True
        
        while self.running:
            try:
                # Pull messages from PubSub
                messages = await pubsub.pull_messages(max_messages=10)
                
                if not messages:
                    await asyncio.sleep(1)
                    continue
                
                # Process messages
                for message in messages:
                    await self.process_job(message.data)
                    await message.ack()
                    
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop the worker."""
        logger.info("Stopping ingestion worker...")
        self.running = False
    
    async def process_job(self, job_data: Dict[str, Any]):
        """Process an ingestion job."""
        try:
            action = job_data.get("action")
            logger.info(f"Processing job: {action}")
            
            if action == "link_ingest":
                await self.handle_link_ingest(job_data)
            elif action == "csv_row":
                await self.handle_csv_row(job_data)
            elif action == "gdrive_sync":
                await self.handle_gdrive_sync(job_data)
            else:
                logger.warning(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Job processing failed: {e}")
            await self.audit_failure(job_data, str(e))
    
    async def handle_link_ingest(self, job_data: Dict[str, Any]):
        """Handle single link ingestion."""
        source_uri = job_data["source_uri"]
        title = job_data["title"]
        doc_type = job_data["doc_type"]
        created_by = job_data["created_by"]
        
        # Generate document ID
        doc_id = f"{doc_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(source_uri) % 10000:04d}"
        
        try:
            # Fetch document from source
            doc_content = await self.fetch_source(source_uri)
            
            # Upload to GCS
            gcs_uri = await self.upload_to_gcs(doc_content, doc_id, title)
            
            # Process document (DocAI or Vision)
            if self.is_image_file(source_uri):
                parsed_content = await vision.extract_text(doc_content)
                media_type = MediaType.IMAGE
            else:
                parsed_content = await docai.extract_text(doc_content)
                media_type = MediaType.DOCUMENT
            
            # Generate chunks
            chunks = self.chunk_text(parsed_content)
            
            # Generate embeddings and upsert to vector search
            vector_ids = await self.upsert_vectors(chunks, doc_id)
            
            # Run DLP scan
            dlp_result = await self.scan_content(parsed_content)
            
            # Create document metadata
            metadata = DocumentMetadata(
                doc_id=doc_id,
                media_type=media_type,
                doc_type=DocType(doc_type),
                title=title,
                uri=gcs_uri,
                source_ref=f"source:{source_uri}",
                status=DocumentStatus.INDEXED if dlp_result["status"] == "passed" else DocumentStatus.QUARANTINED,
                required_fields_ok=True,
                dlp_scan=dlp_result,
                embeddings={"text": {"count": len(chunks)}},
                created_by=created_by,
                topics=job_data.get("tags", [])
            )
            
            # Save metadata to Firestore
            await firestore.save_document_metadata(metadata)
            
            # Audit success
            await self.audit_success(job_data, doc_id)
            
        except Exception as e:
            logger.error(f"Link ingest failed for {source_uri}: {e}")
            await self.audit_failure(job_data, str(e))
    
    async def handle_csv_row(self, job_data: Dict[str, Any]):
        """Handle CSV row ingestion."""
        await self.handle_link_ingest(job_data)
    
    async def handle_gdrive_sync(self, job_data: Dict[str, Any]):
        """Handle Google Drive sync."""
        folder_ids = job_data["folder_ids"]
        recursive = job_data.get("recursive", True)
        initiated_by = job_data["initiated_by"]
        
        try:
            for folder_id in folder_ids:
                # List files in Drive folder
                files = await drive.list_files(folder_id, recursive=recursive)
                
                for file_info in files:
                    # Create ingestion job for each file
                    ingest_job = {
                        "action": "link_ingest",
                        "title": file_info["name"],
                        "doc_type": self.infer_doc_type(file_info["name"]),
                        "source_uri": f"drive:{file_info['id']}",
                        "created_by": initiated_by,
                        "tags": []
                    }
                    
                    await pubsub.publish_ingestion_job(ingest_job)
            
            # Audit sync completion
            await self.audit_success(job_data, f"synced {len(folder_ids)} folders")
            
        except Exception as e:
            logger.error(f"Drive sync failed: {e}")
            await self.audit_failure(job_data, str(e))
    
    async def fetch_source(self, source_uri: str) -> bytes:
        """Fetch document content from source URI."""
        if source_uri.startswith("drive:"):
            file_id = source_uri.replace("drive:", "")
            return await drive.download_file(file_id)
        elif source_uri.startswith("gs://"):
            return await gcs.download_file(source_uri)
        elif source_uri.startswith("http"):
            # Handle HTTP URLs
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(source_uri)
                response.raise_for_status()
                return response.content
        else:
            raise ValueError(f"Unsupported source URI: {source_uri}")
    
    async def upload_to_gcs(self, content: bytes, doc_id: str, title: str) -> str:
        """Upload document content to GCS."""
        bucket_name = os.getenv("GCS_DOC_BUCKET")
        filename = f"{doc_id}/{title}"
        
        await gcs.upload_file(content, bucket_name, filename)
        return f"gs://{bucket_name}/{filename}"
    
    def is_image_file(self, uri: str) -> bool:
        """Check if URI points to an image file."""
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        return any(uri.lower().endswith(ext) for ext in image_extensions)
    
    def chunk_text(self, text: str) -> List[str]:
        """Chunk text for embedding."""
        # Simple chunking by tokens (approximate)
        max_chunk_size = 1000
        words = text.split()
        chunks = []
        
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) > max_chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    async def upsert_vectors(self, chunks: List[str], doc_id: str) -> List[str]:
        """Generate embeddings and upsert to vector search."""
        vector_ids = []
        
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = await vector_search.generate_embedding(chunk)
            
            # Upsert to vector search
            vector_id = f"{doc_id}-chunk-{i}"
            await vector_search.upsert_vector(
                vector_id=vector_id,
                embedding=embedding,
                metadata={
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "text": chunk
                }
            )
            vector_ids.append(vector_id)
        
        return vector_ids
    
    async def scan_content(self, content: str) -> Dict[str, Any]:
        """Run DLP scan on content."""
        # Placeholder for DLP scanning
        # In production, use Google Cloud DLP API
        return {
            "status": "passed",
            "findings": []
        }
    
    def infer_doc_type(self, filename: str) -> str:
        """Infer document type from filename."""
        filename_lower = filename.lower()
        
        if "sow" in filename_lower or "statement" in filename_lower:
            return "sow"
        elif "timeline" in filename_lower or "schedule" in filename_lower:
            return "timeline"
        elif "deliverable" in filename_lower or "delivery" in filename_lower:
            return "deliverable"
        else:
            return "misc"
    
    async def audit_success(self, job_data: Dict[str, Any], result: str):
        """Log successful job processing."""
        audit_entry = {
            "job_id": job_data.get("job_id"),
            "action": job_data.get("action"),
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow(),
            "created_by": job_data.get("created_by")
        }
        
        await firestore.save_audit_entry(audit_entry)
        logger.info(f"Job success: {audit_entry}")
    
    async def audit_failure(self, job_data: Dict[str, Any], error: str):
        """Log failed job processing."""
        audit_entry = {
            "job_id": job_data.get("job_id"),
            "action": job_data.get("action"),
            "status": "failure",
            "error": error,
            "timestamp": datetime.utcnow(),
            "created_by": job_data.get("created_by")
        }
        
        await firestore.save_audit_entry(audit_entry)
        logger.error(f"Job failure: {audit_entry}")


async def main():
    """Main worker entry point."""
    worker = IngestionWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
