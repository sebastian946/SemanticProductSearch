import json

from app.api.get_products import RAW_DATA_PATH
from app.core.db import connection
from app.search.embeddings import embed

BATCH_SIZE = 64

INSERT_QUERY = """
    INSERT INTO reviews (product_id, rating, comment, language, embedding)
    VALUES (%s, %s, %s, %s, %s)
"""


def load_products() -> list[dict]:
    return json.loads(RAW_DATA_PATH.read_text(encoding="utf-8"))


def flatten_reviews(products: list[dict]) -> list[dict]:
    flat = []
    for product in products:
        for review in product.get("reviews", []):
            flat.append(
                {
                    "product_id": product["id"],
                    "rating": review["rating"],
                    "comment": review["comment"],
                    "language": "en",
                }
            )
    return flat


def reviews_ingest(products: list[dict] | None = None) -> int:
    if products is None:
        products = load_products()

    reviews = flatten_reviews(products)
    product_ids = {review["product_id"] for review in reviews}

    cur = connection()
    total = 0

    try:
        # idempotente: las reviews de DummyJSON no traen un id propio, así
        # que en vez de un ON CONFLICT por id, borramos y recargamos las
        # reviews de los productos que estamos por re-ingerir.
        cur.executemany(
            "DELETE FROM reviews WHERE product_id = %s",
            [(product_id,) for product_id in product_ids],
        )

        for start in range(0, len(reviews), BATCH_SIZE):
            batch = reviews[start : start + BATCH_SIZE]
            texts = [review["comment"] for review in batch]
            vectors = embed(texts)

            for review, vector in zip(batch, vectors):
                cur.execute(
                    INSERT_QUERY,
                    (
                        review["product_id"],
                        review["rating"],
                        review["comment"],
                        review["language"],
                        vector,
                    ),
                )

            cur.connection.commit()
            total += len(batch)
            print(f"Lote procesado: {total}/{len(reviews)}")
    finally:
        cur.connection.close()

    return total


if __name__ == "__main__":
    inserted = reviews_ingest()

    cur = connection()
    try:
        cur.execute("SELECT count(*) AS total FROM reviews")
        row = cur.fetchone()
        total_en_db = row["total"] if row else 0
    finally:
        cur.connection.close()

    print(f"Reviews procesadas en esta corrida: {inserted}")
    print(f"Total actual en reviews: {total_en_db}")
