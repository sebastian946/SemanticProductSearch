def build_metadata(product: dict) -> dict:
    return {
        "price": float(product["price"]),
        "category": str(product["category"]),
        "rating": float(product["rating"]),
        "stock": int(product["stock"]),
        "tags": list(product["tags"]),
        "brand": str(product.get("brand") or ""),
        "thumbnail": str(product["thumbnail"]),
    }


def build_page_content(product: dict) -> str:
    return f"Title: {product['title']}\nDescription: {product['description']}"


def build_documents(products: list[dict]) -> list[dict]:
    return [
        {
            "metadata": build_metadata(product),
            "page_content": build_page_content(product),
        }
        for product in products
    ]
