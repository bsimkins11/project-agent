"""ADK planner for Project Agent."""

from typing import Dict, Any, List
from packages.shared.clients.vector_search import VectorSearchClient
from packages.shared.clients.firestore import FirestoreClient


class ADKPlanner:
    """Agent Development Kit planner for query processing."""
    
    def __init__(self):
        self.vector_search = VectorSearchClient()
        self.firestore = FirestoreClient()
    
    async def process_query(self, query: str, filters: Dict[str, Any], max_results: int, user_id: str) -> Dict[str, Any]:
        """
        Process user query using ADK planner.
        
        Args:
            query: User query string
            filters: Query filters
            max_results: Maximum results to return
            user_id: User identifier
            
        Returns:
            Query results with answer and snippets
        """
        try:
            # Generate query embedding
            query_embedding = await self.vector_search.generate_embedding(query)
            
            # Search vectors
            search_results = await self.vector_search.search_vectors(
                query_embedding=query_embedding,
                filters=filters,
                max_results=max_results
            )
            
            # Fetch snippets for results
            snippets = []
            for result in search_results:
                snippet = await self.fetch_snippets(
                    doc_id=result["metadata"]["doc_id"],
                    chunk_index=result["metadata"]["chunk_index"],
                    text=result["metadata"]["text"]
                )
                snippets.append(snippet)
            
            # Compose answer (placeholder for now)
            answer = self.compose_answer(query, snippets)
            
            return {
                "answer": answer,
                "snippets": snippets,
                "total_results": len(snippets)
            }
            
        except Exception as e:
            # Return error response
            return {
                "answer": f"I encountered an error while processing your query: {str(e)}",
                "snippets": [],
                "total_results": 0
            }
    
    def compose_answer(self, query: str, snippets: List[Dict[str, Any]]) -> str:
        """Compose AI answer from query and snippets."""
        # Placeholder implementation
        # In production, use a language model to generate contextual answers
        
        if not snippets:
            return "I couldn't find any relevant information in the knowledge base for your query."
        
        # Simple template-based answer for now
        answer = f"Based on your query '{query}', I found {len(snippets)} relevant document(s):\n\n"
        
        for i, snippet in enumerate(snippets, 1):
            answer += f"{i}. {snippet['title']} - {snippet['excerpt'][:200]}...\n"
        
        return answer
    
    async def fetch_snippets(self, doc_id: str, chunk_index: int, text: str) -> Dict[str, Any]:
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
