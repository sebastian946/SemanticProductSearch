from app.core.db import connection
from app.search.embeddings import embed

RATING_MIN = 1
RATING_MAX = 5


def _product_exists(cur, product_id: int) -> bool:
    cur.execute("SELECT 1 FROM products WHERE id = %s", (product_id,))
    return cur.fetchone() is not None


def add_review(
    product_id: int,
    rating: int,
    comment: str,
    language: str = "es",
) -> dict:
    if not isinstance(rating, int) or not (RATING_MIN <= rating <= RATING_MAX):
        raise ValueError(
            f"rating debe ser un entero entre {RATING_MIN} y {RATING_MAX}, "
            f"se recibió: {rating!r}"
        )
    if not comment or not comment.strip():
        raise ValueError("comment no puede estar vacío")

    comment = comment.strip()
    review_vector = embed([comment])[0]

    cur = connection()
    try:
        if not _product_exists(cur, product_id):
            raise ValueError(f"no existe un producto con id {product_id}")

        cur.execute(
            """
            INSERT INTO reviews (product_id, rating, comment, language, embedding)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, product_id, rating, comment, language, created_at
            """,
            (product_id, rating, comment, language, review_vector),
        )
        review = cur.fetchone()
        cur.connection.commit()
    finally:
        cur.connection.close()

    return review


def get_reviews(product_id: int) -> list[dict]:
    cur = connection()
    try:
        if not _product_exists(cur, product_id):
            raise ValueError(f"no existe un producto con id {product_id}")

        cur.execute(
            """
            SELECT id, product_id, rating, comment, language, created_at
            FROM reviews
            WHERE product_id = %s
            ORDER BY created_at DESC, id DESC
            """,
            (product_id,),
        )
        return cur.fetchall()
    finally:
        cur.connection.close()
