"""Vector Search client for Project Agent."""

import os
from typing import List, Dict, Any, Optional
from google.cloud import aiplatform
import numpy as np


class VectorSearchClient:
    """Client for Vertex AI Vector Search operations."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.location = os.getenv("REGION", "us-central1")
        self.index_id = os.getenv("VECTOR_SEARCH_INDEX_ID")
        
        # Initialize AI Platform
        aiplatform.init(project=self.project_id, location=self.location)
        
        # Initialize the index if available
        if self.index_id:
            try:
                self.index = aiplatform.MatchingEngineIndex(
                    index_name=f"projects/{self.project_id}/locations/{self.location}/indexes/{self.index_id}"
                )
            except Exception as e:
                print(f"⚠️  Could not initialize vector search index: {e}")
                self.index = None
        else:
            self.index = None
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using a simple method.
        In production, this would use a proper embedding model.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        # Simple hash-based embedding for demo purposes
        # In production, use a proper embedding model like text-embedding-ada-002
        import hashlib
        
        # Create a deterministic hash
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to 768-dimensional vector (common embedding size)
        embedding = []
        for i in range(0, len(hash_bytes), 4):
            # Take 4 bytes at a time and convert to float
            if i + 3 < len(hash_bytes):
                val = int.from_bytes(hash_bytes[i:i+4], byteorder='big')
                # Normalize to [-1, 1] range
                normalized = (val / (2**31 - 1)) * 2 - 1
                embedding.append(normalized)
        
        # Pad or truncate to exactly 768 dimensions
        while len(embedding) < 768:
            embedding.append(0.0)
        
        return embedding[:768]
    
    async def upsert_vector(self, vector_id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Upsert vector to vector search index."""
        try:
            if not self.index:
                print("⚠️  No vector search index configured, skipping upsert")
                return True
            
            # For now, just simulate success
            print(f"📤 Upserting vector {vector_id} to index")
            return True
            
        except Exception as e:
            print(f"❌ Error upserting vector: {e}")
            return False
    
    async def search_vectors(self, query_embedding: List[float], filters: Dict[str, Any], max_results: int = 10) -> List[Dict[str, Any]]:
        """Search vectors in the index."""
        try:
            if not self.index:
                print("⚠️  No vector search index configured, returning mock results")
                # Return mock results for testing
                return [
                    {
                        "id": "mock-001",
                        "score": 0.95,
                        "metadata": {
                            "doc_id": "doc-001",
                            "chunk_index": 0,
                            "text": "Sample document content",
                            "page": 1
                        }
                    }
                ]
            
            # For now, return mock results
            print(f"🔍 Searching vectors with max_results={max_results}")
            
            results = []
            for i in range(min(max_results, 5)):
                results.append({
                    "id": f"vector-{i+1}",
                    "score": 0.9 - (i * 0.1),
                    "metadata": {
                        "doc_id": f"doc-{i+1:03d}",
                        "chunk_index": i,
                        "text": f"Sample document {i+1} content",
                        "page": i + 1
                    }
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching vectors: {e}")
            return []
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for embedding.
        
        Args:
            text: Input text
            chunk_size: Maximum chunk size
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at word boundary
            if end < len(text):
                # Find the last space before the end
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
