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

from cachetools import LRUCache
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

_model: SentenceTransformer | None = None

# Caché en memoria (no Redis) a propósito: la app corre en un solo proceso
# y el mismo texto siempre produce el mismo vector, así que un LRU local
# alcanza y evita infra extra. Si esto escalara a varios procesos/replicas,
# el mismo mapeo texto->vector se movería a Redis sin cambiar la interfaz.
_embedding_cache: LRUCache = LRUCache(maxsize=2048)


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    missing = [text for text in texts if text not in _embedding_cache]
    if missing:
        model = _get_model()
        vectors = model.encode(missing, normalize_embeddings=True).tolist()
        for text, vector in zip(missing, vectors):
            _embedding_cache[text] = vector
    return [_embedding_cache[text] for text in texts]
