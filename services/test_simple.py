"""Simple test FastAPI app to verify setup."""

from fastapi import FastAPI

app = FastAPI(title="Test API")

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Project Agent test service running"}

@app.get("/")
async def root():
    return {"message": "Project Agent is alive!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
