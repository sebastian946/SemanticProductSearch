from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

EMBEDDING_DIM = 384  # ver app/search/embeddings.py


class Products(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    image_url = Column(String)
    product_url = Column(String)
    price = Column(Float, index=True)
    category = Column(String, index=True)
    rating = Column(Float, index=True)
    stock = Column(Integer, index=True)
    tags = Column(ARRAY(String), index=False)
    brand = Column(String, index=True)
    thumbnail = Column(String, index=False)
    embedding = Column(Vector(EMBEDDING_DIM))

class Reviews(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(String)
    language = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    embedding = Column(Vector(EMBEDDING_DIM))


class ProductResult(BaseModel):
    id: int
    title: str
    description: str
    price: float
    image_url: str | None
    product_url: str
    score: float

    model_config = ConfigDict(from_attributes=True)


class SearchFilters(BaseModel):
    category: str | None = None
    brand: str | None = None
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: SearchFilters | None = None
    include_recommendation: bool = True

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query no puede estar vacío")
        return value.strip()


class Recommendation(BaseModel):
    answer: str
    tool_calls: list[str] = []


class SearchResponse(BaseModel):
    results: list[ProductResult]
    recommendation: Recommendation | None = None
    recommendation_error: str | None = None


Index(
    "ix_products_embedding_hnsw",
    Products.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)

Index(
    "ix_reviews_embedding_hnsw",
    Reviews.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
