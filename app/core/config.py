import sys

from pydantic import SecretStr, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    environment: str = Field(default="development")
    langsmith_tracing: bool = Field(default=False)
    langsmith_endpoint: str = Field(default="https://api.smith.langchain.com")
    langsmith_api_key: SecretStr
    langsmith_project: str = Field(default="SemanticProductSearch")
    anthropic_api_key: SecretStr
    database_url: str = Field(default="sqlite:///./semantic_product_search.db")
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    top_k: int = Field(default=5)

    model_config = SettingsConfigDict(env_file=".env")

try:
    settings = AppSettings()  # type: ignore[call-arg]
except ValidationError as e:
    print("Error loading settings. Missing or invalid environment variables:", file=sys.stderr)
    for error in e.errors():
        loc = ".".join(str(part) for part in error.get("loc", ()))
        msg = error.get("msg", "")
        print(f"  - {loc}: {msg}", file=sys.stderr)
    sys.exit(1)