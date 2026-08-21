from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Column, Float, Index, Integer, String
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


Index(
    "ix_products_embedding_hnsw",
    Products.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
