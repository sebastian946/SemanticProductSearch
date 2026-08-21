"""Decisión de modelo de embeddings (PROD-8).

Elegido: `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers), local.

Por qué:
- Multilingüe (50+ idiomas): un query en español puede matchear productos
  descritos en inglés sin traducción explícita — el requisito central del
  ticket.
- Local y gratis: sin costo por request ni dependencia de una API externa.
- Liviano (~470MB) y rápido en CPU, a diferencia de alternativas locales más
  grandes como `multilingual-e5-large` (~2.2GB, mejor calidad pero más lento
  sin GPU).
- Se descartó `voyage-law-2` (usado en una prueba anterior en
  `app/agent/embdedding.py`): es un modelo de dominio legal en inglés, no
  multilingüe.

Dimensión de salida: 384 — debe coincidir con EMBEDDING_DIM en
app/models/schemas.py y con la columna `vector(N)` de la tabla `products`.
"""

from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()
