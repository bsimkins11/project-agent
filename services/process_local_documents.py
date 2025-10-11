"""Process local documents for Project Agent testing."""

import os
import sys
import asyncio
import mimetypes
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from packages.shared.clients.gcs import GCSClient
from packages.shared.clients.documentai import DocumentAIClient
from packages.shared.clients.firestore import FirestoreClient
from packages.shared.clients.vector_search import VectorSearchClient
from packages.shared.schemas.document import DocumentMetadata

class LocalDocumentProcessor:
    """Process local documents and add them to Project Agent."""
    
    def __init__(self):
        self.gcs_client = GCSClient()
        self.docai_client = DocumentAIClient()
        self.firestore_client = FirestoreClient()
        self.vector_client = VectorSearchClient()
        
        # Supported file types
        self.supported_types = {
            '.pdf': 'PDF',
            '.docx': 'DOCX',
            '.txt': 'TXT',
            '.md': 'MD',
            '.html': 'HTML',
            '.htm': 'HTML'
        }
    
    def get_mime_type(self, file_path: str) -> str:
        """Get MIME type for a file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def get_doc_type(self, file_path: str) -> str:
        """Get document type from file extension."""
        ext = Path(file_path).suffix.lower()
        return self.supported_types.get(ext, 'TXT')
    
    async def process_document(self, file_path: str) -> dict:
        """
        Process a single document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Processing results
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            print(f"\n📄 Processing: {file_path.name}")
            print(f"   Path: {file_path}")
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            print(f"   Size: {len(file_content):,} bytes")
            
            # Get file info
            doc_type = self.get_doc_type(str(file_path))
            mime_type = self.get_mime_type(str(file_path))
            
            print(f"   Type: {doc_type} ({mime_type})")
            
            # Upload to GCS
            import uuid
            doc_id = str(uuid.uuid4())
            bucket_name = os.getenv("GCS_DOC_BUCKET", "ta-test-docs-dev")
            gcs_path = f"documents/{doc_id}/{file_path.name}"
            
            print(f"📤 Uploading to GCS...")
            gcs_url = await self.gcs_client.upload_file(
                bucket_name=bucket_name,
                file_path=gcs_path,
                file_content=file_content,
                content_type=mime_type
            )
            
            print(f"✅ Uploaded to: {gcs_url}")
            
            # Process with Document AI
            print(f"🤖 Processing with Document AI...")
            processing_result = self.docai_client.process_document(
                file_content=file_content,
                mime_type=mime_type
            )
            
            print(f"✅ Document AI processing completed")
            print(f"   Text length: {len(processing_result['text'])} characters")
            print(f"   Confidence: {processing_result['confidence']:.2f}")
            
            # Create document metadata
            doc_metadata = DocumentMetadata(
                id=doc_id,
                title=file_path.stem,  # Filename without extension
                type=doc_type,
                size=len(file_content),
                uri=gcs_url,
                status="processed",
                upload_date="2024-01-15T10:30:00Z",
                processing_result=processing_result
            )
            
            # Save to Firestore
            print(f"💾 Saving to Firestore...")
            await self.firestore_client.save_document(doc_metadata)
            print(f"✅ Document metadata saved: {doc_id}")
            
            # Create text chunks and embeddings
            print(f"✂️  Creating text chunks...")
            text_chunks = self.vector_client.chunk_text(
                processing_result['text'],
                chunk_size=500,
                overlap=50
            )
            
            print(f"✅ Created {len(text_chunks)} chunks")
            
            # Generate embeddings and index
            print(f"🔍 Generating embeddings and indexing...")
            vector_ids = []
            
            for i, chunk in enumerate(text_chunks):
                if chunk.strip():  # Skip empty chunks
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
                        "page": min(i + 1, processing_result.get('page_count', 1))
                    }
                    
                    # Upsert to vector search
                    success = await self.vector_client.upsert_vector(vector_id, embedding, metadata)
                    if success:
                        vector_ids.append(vector_id)
                        print(f"   ✅ Indexed chunk {i+1}/{len(text_chunks)}")
            
            # Update document with vector IDs
            doc_metadata.status = "indexed"
            doc_metadata.__dict__['vector_ids'] = vector_ids
            await self.firestore_client.save_document(doc_metadata)
            
            print(f"🎉 Document processing completed!")
            print(f"   Document ID: {doc_id}")
            print(f"   Chunks: {len(text_chunks)}")
            print(f"   Vectors: {len(vector_ids)}")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "title": doc_metadata.title,
                "chunks": len(text_chunks),
                "vectors": len(vector_ids),
                "gcs_url": gcs_url
            }
            
        except Exception as e:
            print(f"❌ Failed to process {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "file_path": str(file_path),
                "error": str(e)
            }
    
    async def process_directory(self, directory_path: str) -> dict:
        """
        Process all supported documents in a directory.
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            Processing summary
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")
        
        print(f"📁 Processing directory: {directory}")
        
        # Find all supported files
        supported_files = []
        for ext in self.supported_types.keys():
            supported_files.extend(directory.glob(f"*{ext}"))
            supported_files.extend(directory.glob(f"*{ext.upper()}"))
        
        print(f"📄 Found {len(supported_files)} supported documents")
        
        if not supported_files:
            print("❌ No supported documents found in directory")
            return {"success": False, "error": "No supported documents found"}
        
        # Process each document
        results = []
        successful = 0
        failed = 0
        
        for file_path in supported_files:
            result = await self.process_document(file_path)
            results.append(result)
            
            if result["success"]:
                successful += 1
            else:
                failed += 1
        
        print(f"\n📊 Processing Summary:")
        print(f"   Total files: {len(supported_files)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        
        return {
            "success": successful > 0,
            "total_files": len(supported_files),
            "successful": successful,
            "failed": failed,
            "results": results
        }

async def main():
    """Main function to process documents."""
    processor = LocalDocumentProcessor()
    
    # Check if directory argument provided
    if len(sys.argv) > 1:
        directory_path = sys.argv[1]
        await processor.process_directory(directory_path)
    else:
        print("📁 Local Document Processor for Project Agent")
        print("=" * 50)
        print("Usage:")
        print("  python process_local_documents.py <directory_path>")
        print("\nExample:")
        print("  python process_local_documents.py ./test_documents")
        print("\nSupported file types:")
        for ext, doc_type in processor.supported_types.items():
            print(f"  {ext} -> {doc_type}")

if __name__ == "__main__":
    asyncio.run(main())
