from langchain_postgres import PGVector
from langchain_voyageai import VoyageAIEmbeddings

from app.core.config import settings

VOYAGE_API_KEY = settings.voyage_api_key

class EmbeddingConfig:
    def __init__(self) -> None:
        self.embedding = []

    def config_embedding(self):
        self.embedding = VoyageAIEmbeddings(
            api_key=VOYAGE_API_KEY,
            model="voyage-law-2",
        )

    def vector_store(self):
        self.vector_store = PGVector(
            embeddings=self.embedding,
            collection_name="Agent Embedding",
            connection=""
        )
    