from fastapi import APIRouter

from app.data.storage import store

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/products")
async def list_products():
    return store.get_data()
