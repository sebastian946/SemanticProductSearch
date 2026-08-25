import json

from app.api.get_products import RAW_DATA_PATH
from app.catalog.mapper import build_documents
from app.core.db import connection
from app.search.embeddings import embed

BATCH_SIZE = 64

UPSERT_QUERY = """
    INSERT INTO products (
        id, title, description, image_url, product_url,
        price, category, rating, stock, tags, brand, thumbnail, embedding
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET
        title = EXCLUDED.title,
        description = EXCLUDED.description,
        image_url = EXCLUDED.image_url,
        product_url = EXCLUDED.product_url,
        price = EXCLUDED.price,
        category = EXCLUDED.category,
        rating = EXCLUDED.rating,
        stock = EXCLUDED.stock,
        tags = EXCLUDED.tags,
        brand = EXCLUDED.brand,
        thumbnail = EXCLUDED.thumbnail,
        embedding = EXCLUDED.embedding
"""


def load_products() -> list[dict]:
    return json.loads(RAW_DATA_PATH.read_text(encoding="utf-8"))


def ingest(products: list[dict] | None = None) -> int:
    if products is None:
        products = load_products()

    documents = build_documents(products)
    cur = connection()
    total = 0

    for start in range(0, len(products), BATCH_SIZE):
        batch_products = products[start : start + BATCH_SIZE]
        batch_documents = documents[start : start + BATCH_SIZE]
        texts = [doc["page_content"] for doc in batch_documents]
        vectors = embed(texts)

        for product, doc, vector in zip(batch_products, batch_documents, vectors):
            metadata = doc["metadata"]
            images = product.get("images") or []
            cur.execute(
                UPSERT_QUERY,
                (
                    product["id"],
                    product["title"],
                    product["description"],
                    images[0] if images else None,
                    f"https://dummyjson.com/products/{product['id']}",
                    metadata["price"],
                    metadata["category"],
                    metadata["rating"],
                    metadata["stock"],
                    metadata["tags"],
                    metadata["brand"],
                    metadata["thumbnail"],
                    vector,
                ),
            )

        cur.connection.commit()
        total += len(batch_products)
        print(f"Lote procesado: {total}/{len(products)}")

    return total


if __name__ == "__main__":
    inserted = ingest()

    cur = connection()
    cur.execute("SELECT count(*) AS total FROM products")
    row = cur.fetchone()
    total_en_db = row["total"] if row else 0

    print(f"Productos procesados en esta corrida: {inserted}")
    print(f"Total actual en products: {total_en_db}")
