from app.core.db import connection
from app.search.embeddings import embed

QUERY_SEMANTIC = """
    SELECT
        id, title, description, image_url, product_url,
        price, category, rating, stock, tags, brand, thumbnail,
        embedding <=> %s::vector AS distance
    FROM products
    ORDER BY embedding <=> %s::vector
    LIMIT %s
"""


def search(query: str, top_k: int = 5) -> list[dict]:
    query_vector = embed([query])[0]

    cur = connection()
    cur.execute(QUERY_SEMANTIC, (query_vector, query_vector, top_k))
    results = cur.fetchall()
    cur.connection.close()

    for row in results:
        row["similarity"] = 1 - row["distance"]

    return results
