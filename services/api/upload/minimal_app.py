"""Minimal Upload API for document ingestion."""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Project Agent Upload API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for processing."""
    # For now, just return a success response
    return {
        "message": f"Document '{file.filename}' uploaded successfully",
        "file_id": f"doc-{file.filename}-001",
        "status": "uploaded",
        "size": len(await file.read()) if hasattr(file, 'read') else 0
    }

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
