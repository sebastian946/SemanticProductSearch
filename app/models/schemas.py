from pydantic import BaseModel, Field


class ProductSchema(BaseModel):
    id: int = Field(..., description="The unique identifier of the product")
    title: str = Field(..., description="The title of the product")
    description: str | None = Field(
        None, description="A brief description of the product"
    )
    price: float = Field(..., description="The price of the product")
    category: str = Field(..., description="The category of the product")