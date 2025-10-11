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
        Process user query using ADK planner with RBAC filtering.
        
        CRITICAL: Filters documents by user's accessible projects/clients BEFORE
        composing answer to prevent information leakage.
        
        Args:
            query: User query string
            filters: Query filters (includes user_project_ids, user_client_ids, user_role)
            max_results: Maximum results to return
            user_id: User identifier
            
        Returns:
            Query results with answer and snippets (only from accessible documents)
        """
        try:
            # Extract RBAC context from filters
            user_project_ids = filters.get("user_project_ids", [])
            user_client_ids = filters.get("user_client_ids", [])
            user_role = filters.get("user_role", "")
            
            # Generate query embedding
            query_embedding = await self.vector_search.generate_embedding(query)
            
            # Search vectors (get more results than needed for filtering)
            search_results = await self.vector_search.search_vectors(
                query_embedding=query_embedding,
                filters=filters,
                max_results=max_results * 3  # Get 3x results to account for RBAC filtering
            )
            
            # Fetch snippets and filter by RBAC BEFORE composing answer
            all_snippets = []
            for result in search_results:
                doc_id = result["metadata"]["doc_id"]
                
                # Get document metadata to check project/client assignment
                doc_metadata = await self.firestore.get_document_metadata(doc_id)
                
                # CRITICAL: Filter by RBAC before including in snippets
                if await self._check_document_access(doc_metadata, user_project_ids, user_client_ids, user_role):
                    snippet = await self.fetch_snippets(
                        doc_id=doc_id,
                        chunk_index=result["metadata"]["chunk_index"],
                        text=result["metadata"]["text"]
                    )
                    all_snippets.append(snippet)
                    
                    # Stop once we have enough accessible snippets
                    if len(all_snippets) >= max_results:
                        break
            
            # Compose answer ONLY from accessible snippets
            answer = self.compose_answer(query, all_snippets)
            
            return {
                "answer": answer,
                "snippets": all_snippets,
                "total_results": len(all_snippets)
            }
            
        except Exception as e:
            # Return error response
            return {
                "answer": f"I encountered an error while processing your query: {str(e)}",
                "snippets": [],
                "total_results": 0
            }
    
    async def _check_document_access(self, doc_metadata: Any, user_project_ids: List[str], user_client_ids: List[str], user_role: str) -> bool:
        """
        Check if user has access to document based on RBAC rules.
        
        CRITICAL SECURITY FUNCTION - This prevents information leakage.
        
        Args:
            doc_metadata: Document metadata
            user_project_ids: User's accessible project IDs
            user_client_ids: User's accessible client IDs
            user_role: User's role (super_admin has all access)
            
        Returns:
            True if user can access document, False otherwise
        """
        if not doc_metadata:
            return False
        
        # Super admins have access to everything
        if user_role == "super_admin":
            return True
        
        # Check project access
        doc_project_id = getattr(doc_metadata, 'project_id', None)
        if doc_project_id and doc_project_id in user_project_ids:
            return True
        
        # Check client access
        doc_client_id = getattr(doc_metadata, 'client_id', None)
        if doc_client_id and doc_client_id in user_client_ids:
            return True
        
        # Default: no access
        return False
    
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
