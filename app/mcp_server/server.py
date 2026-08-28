import json

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.tools.base import ToolError

from app.reviews import logic as reviews_logic
from app.search.semantic_search import search_formatted

mcp = MCPServer("semantic-product-search")


@mcp.tool()
def search_products(
    query: str,
    top_k: int = 5,
    category: str | None = None,
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """Busca productos por significado, no por palabras exactas.

    Usa búsqueda semántica (embeddings multilingües): el query puede estar en
    español o inglés y describir una necesidad vaga ("algo para mantener el
    café caliente") — no hace falta conocer el nombre del producto. Devuelve
    los top_k productos más relevantes con título, descripción, precio,
    imagen, link y score de similitud (0 a 1, más alto = más relevante).

    Usa los filtros opcionales para restringir por categoría exacta
    (ej. "beauty", "laptops", "groceries"), marca, o rango de precio.
    """
    results = search_formatted(
        query,
        top_k=top_k,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
    )
    return [product.model_dump() for product in results]


@mcp.tool()
def get_reviews(product_id: int) -> list[dict]:
    """Devuelve las reseñas de un producto, de la más reciente a la más vieja.

    Cada reseña incluye rating (1-5), comentario, idioma y fecha. Falla con
    un mensaje claro si el producto no existe. Usa search_products primero
    para obtener el product_id.
    """
    try:
        reviews = reviews_logic.get_reviews(product_id)
    except ValueError as e:
        raise ToolError(str(e)) from e
    return [_serialize_review(review) for review in reviews]


@mcp.tool()
def add_review(
    product_id: int,
    rating: int,
    comment: str,
    language: str = "es",
) -> dict:
    """Agrega una reseña a un producto y devuelve la reseña creada.

    rating debe ser un entero de 1 a 5 y comment no puede estar vacío.
    Falla con un mensaje claro si el producto no existe o los datos son
    inválidos.
    """
    try:
        review = reviews_logic.add_review(product_id, rating, comment, language)
    except ValueError as e:
        raise ToolError(str(e)) from e
    return _serialize_review(review)


@mcp.resource("catalog://products")
def catalog() -> str:
    """Catálogo completo de productos (id, título, categoría, marca, precio)."""
    from app.core.db import connection

    cur = connection()
    try:
        cur.execute(
            "SELECT id, title, category, brand, price FROM products ORDER BY id"
        )
        rows = cur.fetchall()
    finally:
        cur.connection.close()
    return json.dumps(rows, ensure_ascii=False, indent=2)


def _serialize_review(review: dict) -> dict:
    review = dict(review)
    if review.get("created_at") is not None:
        review["created_at"] = review["created_at"].isoformat()
    return review


if __name__ == "__main__":
    mcp.run()
