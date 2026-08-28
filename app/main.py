from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes, search
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
app.include_router(search.router)


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(Exception)
async def unhandled_error_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"error": "error interno del servidor"}
    )

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