"""Agent tools for Project Agent."""

from typing import Dict, Any, List, Optional
from packages.shared.clients.vector_search import VectorSearchClient
from packages.shared.clients.firestore import FirestoreClient


class VectorSearchTool:
    """Tool for vector search operations."""
    
    def __init__(self):
        self.client = VectorSearchClient()
    
    async def search(self, query_embedding: List[float], filters: Dict[str, Any], max_results: int = 10) -> List[Dict[str, Any]]:
        """Search vectors in the index."""
        return await self.client.search_vectors(query_embedding, filters, max_results)


class SnippetFetcher:
    """Tool for fetching document snippets."""
    
    def __init__(self):
        self.firestore = FirestoreClient()
    
    async def fetch(self, doc_id: str, chunk_index: int, text: str) -> Dict[str, Any]:
        """Fetch document snippet with metadata."""
        # Get document metadata
        metadata = await self.firestore.get_document_metadata(doc_id)
        
        if not metadata:
            return {
                "doc_id": doc_id,
                "title": "Unknown Document",
                "excerpt": text[:200] + "..." if len(text) > 200 else text,
                "uri": "",
                "page": None,
                "thumbnail": None
            }
        
        return {
            "doc_id": doc_id,
            "title": metadata.title,
            "excerpt": text[:200] + "..." if len(text) > 200 else text,
            "uri": metadata.uri,
            "page": chunk_index + 1,  # Approximate page number
            "thumbnail": metadata.thumbnails[0] if metadata.thumbnails else None
        }


# Global tool instances
vector_search_tool = VectorSearchTool()
snippet_fetcher = SnippetFetcher()


async def search_index(query_embedding: List[float], filters: Dict[str, Any], max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search the vector index for relevant documents.
    
    Args:
        query_embedding: Query vector embedding
        filters: Search filters
        max_results: Maximum results to return
        
    Returns:
        List of search results
    """
    return await vector_search_tool.search(query_embedding, filters, max_results)


async def fetch_snippets(doc_id: str, chunk_index: int, text: str) -> Dict[str, Any]:
    """
    Fetch document snippet with metadata.
    
    Args:
        doc_id: Document identifier
        chunk_index: Chunk index within document
        text: Chunk text content
        
    Returns:
        Snippet with metadata
    """
    return await snippet_fetcher.fetch(doc_id, chunk_index, text)
