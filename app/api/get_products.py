import asyncio
import json
from pathlib import Path

import requests

from app.catalog.mapper import build_documents
from app.data.storage import store

DUMMYJSON_URL = "https://dummyjson.com/products"
RAW_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "dummyjson_products.json"


async def get_products():
    response = await asyncio.to_thread(
        requests.get, DUMMYJSON_URL, params={"limit": 0}
    )
    if response.status_code != 200:
        return {
            "error": "Failed to fetch products",
            "status_code": response.status_code,
        }

    products = response.json()["products"]

    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_DATA_PATH.write_text(json.dumps(products, indent=2), encoding="utf-8")

    store.set_data(products)
    store.set_documents(build_documents(products))
    return products
