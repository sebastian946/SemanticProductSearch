from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes
from app.api.get_products import get_products
from app.core.config import settings
from app.core.db import connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Get all the products from the API and store them in memory")
    result = await get_products()
    if isinstance(result, dict) and "error" in result:
        print(f"WARNING: no se pudo cargar el catálogo al iniciar: {result}")
    yield



app = FastAPI(
    title="Semantic Product Search API",
    version="1.0.0",
    description="API for semantic product search using embeddings and pgvector.",
    lifespan=lifespan
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)

@app.get("/health")
def health_check():
    cur = connection()
    try:
        cur.execute("SELECT 1")
    except Exception:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "message": "Database connection failed."},
        )
    finally:
        cur.connection.close()
    return {"status": "ok", "message": "Semantic Product Search API is running."}