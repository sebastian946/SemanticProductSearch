import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.recommender import recommend, stream_recommendation
from app.models.schemas import (
    Recommendation,
    SearchFilters,
    SearchRequest,
    SearchResponse,
)
from app.search.semantic_search import search_formatted

AGENT_TIMEOUT_SECONDS = 120

router = APIRouter(tags=["search"])


def _run_search(request: SearchRequest):
    filters = request.filters or SearchFilters()
    return search_formatted(
        request.query,
        top_k=request.top_k,
        category=filters.category,
        brand=filters.brand,
        min_price=filters.min_price,
        max_price=filters.max_price,
    )


@router.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest) -> SearchResponse:
    results = await asyncio.to_thread(_run_search, request)

    recommendation = None
    recommendation_error = None
    if request.include_recommendation and results:
        # Si el agente (LLM o MCP externo) falla o tarda de más, la request
        # no se cae: se devuelven igual los resultados de búsqueda.
        try:
            outcome = await asyncio.wait_for(
                recommend(request.query), timeout=AGENT_TIMEOUT_SECONDS
            )
            recommendation = Recommendation(**outcome)
        except TimeoutError:
            recommendation_error = "la recomendación excedió el tiempo límite"
        except Exception as e:
            recommendation_error = f"no se pudo generar la recomendación: {e}"

    return SearchResponse(
        results=results,
        recommendation=recommendation,
        recommendation_error=recommendation_error,
    )


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/search/stream")
async def search_stream(request: SearchRequest) -> StreamingResponse:
    async def event_generator():
        yield _sse("status", "buscando productos")
        results = await asyncio.to_thread(_run_search, request)
        yield _sse("results", [product.model_dump() for product in results])

        if request.include_recommendation and results:
            yield _sse("status", "generando recomendación")
            try:
                async for token in stream_recommendation(request.query):
                    yield _sse("token", token)
            except Exception as e:
                yield _sse("error", f"no se pudo generar la recomendación: {e}")

        yield _sse("done", "")

    return StreamingResponse(event_generator(), media_type="text/event-stream")
