from app.core.db import connection
from app.search.embeddings import embed


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
    # sql se arma dinámicamente pero solo con fragmentos fijos definidos
    # arriba (nunca con valores del caller) — los valores siempre van
    # parametrizados en `params`, así que es seguro pese al warning de tipos.
    cur.execute(sql, params)  # type: ignore[arg-type]
    results = cur.fetchall()
    cur.connection.close()

    for row in results:
        row["similarity"] = 1 - row["distance"]

    return results
