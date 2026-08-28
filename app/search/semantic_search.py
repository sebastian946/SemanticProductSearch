from cachetools import TTLCache

from app.core.db import connection
from app.models.schemas import ProductResult
from app.search.embeddings import embed

DESCRIPTION_PREVIEW_LENGTH = 160


def search(
    query: str,
    top_k: int = 5,
    category: str | None = None,
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[dict]:
    query_vector = embed([query])[0]

    filters: list[str] = []
    filter_params: list = []

    if category is not None:
        filters.append("category = %s")
        filter_params.append(category)

    if brand is not None:
        filters.append("brand = %s")
        filter_params.append(brand)

    if min_price is not None:
        filters.append("price >= %s")
        filter_params.append(min_price)

    if max_price is not None:
        filters.append("price <= %s")
        filter_params.append(max_price)

    sql = """
        SELECT
            id, title, description, image_url, product_url,
            price, category, rating, stock, tags, brand, thumbnail,
            embedding <=> %s::vector AS distance
        FROM products
    """
    params: list = [query_vector]

    if filters:
        sql += " WHERE " + " AND ".join(filters)
        params.extend(filter_params)

    sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
    params.extend([query_vector, top_k])

    cur = connection()
    try:
        # sql se arma dinámicamente pero solo con fragmentos fijos definidos
        # arriba (nunca con valores del caller) — los valores siempre van
        # parametrizados en `params`, así que es seguro pese al warning de tipos.
        cur.execute(sql, params)  # type: ignore[arg-type]
        results = cur.fetchall()
    finally:
        cur.connection.close()

    for row in results:
        row["similarity"] = 1 - row["distance"]

    return results


def _short_description(description: str | None) -> str:
    text = description or ""
    if len(text) <= DESCRIPTION_PREVIEW_LENGTH:
        return text
    return text[:DESCRIPTION_PREVIEW_LENGTH].rstrip() + "..."


def to_product_result(row: dict) -> ProductResult:
    return ProductResult(
        id=row["id"],
        title=row["title"],
        description=_short_description(row["description"]),
        price=row["price"],
        image_url=row["image_url"] or row["thumbnail"],
        product_url=row["product_url"],
        score=row["similarity"],
    )


def search_formatted(query: str, top_k: int = 5, **filters) -> list[ProductResult]:
    rows = search(query, top_k=top_k, **filters)
    return [to_product_result(row) for row in rows]


# TTL corto: el catálogo cambia poco, pero un re-ingest debe reflejarse
# en minutos sin reiniciar la app. En memoria y no Redis por la misma
# razón documentada en embeddings.py (un solo proceso).
_search_cache: TTLCache = TTLCache(maxsize=512, ttl=300)


def search_formatted_cached(
    query: str, top_k: int = 5, **filters
) -> tuple[list[ProductResult], bool]:
    """Como search_formatted, pero con caché. Devuelve (resultados, cache_hit)."""
    key = (query, top_k, tuple(sorted(filters.items())))
    if key in _search_cache:
        return _search_cache[key], True
    results = search_formatted(query, top_k=top_k, **filters)
    _search_cache[key] = results
    return results, False
