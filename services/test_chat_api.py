"""Test chat API without authentication."""

import os
import sys
import time
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from packages.shared.schemas import ChatRequest, ChatResponse, Citation
from packages.shared.clients.vector_search import VectorSearchClient
from packages.shared.clients.firestore import FirestoreClient

app = FastAPI(
    title="Project Agent Chat API (Test)",
    description="AI-powered chat with cited answers from document knowledge base - TEST VERSION",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://transparent-agent-test.web.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
vector_client = VectorSearchClient()
firestore_client = FirestoreClient()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process chat query and return AI-generated answer with citations.
    TEST VERSION - No authentication required.
    """
    start_time = time.time()
    
    try:
        print(f"🔍 Processing query: '{request.query}'")
        
        # 1. Generate query embedding
        query_embedding = vector_client.generate_embedding(request.query)
        print(f"📊 Generated query embedding: {len(query_embedding)} dimensions")
        
        # 2. Search vector index for relevant documents
        search_results = await vector_client.search_vectors(
            query_embedding=query_embedding,
            filters=request.filters or {},
            max_results=10
        )
        
        print(f"🔍 Found {len(search_results)} search results")
        
        # 3. Process search results into citations
        citations = []
        for result in search_results:
            metadata = result.get("metadata", {})
            
            # Get document metadata from Firestore
            doc_metadata = None
            if "doc_id" in metadata:
                doc_metadata = await firestore_client.get_document(metadata["doc_id"])
            
            citation = Citation(
                doc_id=metadata.get("doc_id", result["id"]),
                title=doc_metadata.title if doc_metadata else f"Document {metadata.get('doc_id', 'Unknown')}",
                uri=doc_metadata.uri if doc_metadata else f"gs://unknown/{metadata.get('doc_id', 'unknown')}",
                page=metadata.get("page", 1),
                excerpt=metadata.get("text", "No excerpt available")[:200] + "...",
                thumbnail=None
            )
            citations.append(citation)
            print(f"📄 Citation: {citation.title}")
        
        # 4. Generate answer using simple template (in production, use LLM)
        if citations:
            answer = f"Based on your query '{request.query}', I found {len(citations)} relevant documents:\n\n"
            for i, citation in enumerate(citations[:3], 1):  # Show top 3
                answer += f"{i}. **{citation.title}** (Page {citation.page})\n"
                answer += f"   {citation.excerpt}\n\n"
            
            if len(citations) > 3:
                answer += f"... and {len(citations) - 3} more documents."
        else:
            answer = f"I couldn't find any documents related to '{request.query}'. Try rephrasing your question or checking if the relevant documents have been uploaded to the system."
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        print(f"✅ Query processed in {query_time_ms}ms")
        
        return ChatResponse(
            answer=answer,
            citations=citations,
            query_time_ms=query_time_ms,
            total_results=len(search_results)
        )
        
    except Exception as e:
        print(f"❌ Chat processing failed: {e}")
        import traceback
        traceback.print_exc()
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        # Return error response
        return ChatResponse(
            answer=f"I encountered an error while processing your query: {str(e)}",
            citations=[],
            query_time_ms=query_time_ms,
            total_results=0
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chat-api-test"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Project Agent Chat API (Test) is running!", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8087)
