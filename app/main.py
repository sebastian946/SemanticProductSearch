from fastapi import FastAPI, HTTPException
from app.core.config import settings
from app.core.db import connection
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Semantic Product Search API",
              version="1.0.0",
              description="API for semantic product search using embeddings and vector databases.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    try:
        cur = connection()
        cur.execute("SELECT 1")
        cur.connection.close()
    except Exception:
        raise HTTPException(status_code=503, detail={"status": "error", "message": "Database connection failed."})
    return {"status": "ok", "message": "Semantic Product Search API is running."}