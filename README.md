# Semantic Product Search

Buscador semántico de productos: en vez de matchear keywords, entiende la
intención de la query (embeddings + similarity search) y usa un agente para
generar una recomendación sobre el catálogo. El catálogo se expone como
servidor MCP y es consumido por un agente separado.

> 🚧 Proyecto en desarrollo activo. Actualmente en **Fase 1 · Setup backend**.
> Las secciones de arquitectura, demo y decisiones de diseño se completarán
> más adelante, cuando exista un flujo end-to-end funcional.

## Stack

- **API:** FastAPI
- **Agente / orquestación:** LangChain + LangChain Anthropic (Claude)
- **Modelos locales:** Ollama
- **Observabilidad:** LangSmith
- **Config / validación:** Pydantic + Pydantic Settings
- **Base de datos:** Postgres + pgvector (en desarrollo local: SQLite)
- **Gestor de paquetes:** [uv](https://docs.astral.sh/uv/)

## Estructura del proyecto

```
app/
  main.py           # entrypoint de la API
  api/routes.py      # rutas HTTP
  catalog/           # ingesta + modelos de datos del catálogo
  search/             # embeddings + similarity search
  reviews/
  mcp_server/         # servidor MCP (expone el catálogo/búsqueda como tools)
  agent/               # agente que consume el MCP y arma la recomendación
  core/
    config.py         # settings (variables de entorno)
    db.py              # conexión a Postgres/pgvector
  models/
    schemas.py         # modelos Pydantic compartidos
tests/
```

## Setup local

Requisitos: Python >= 3.12 y [uv](https://docs.astral.sh/uv/) instalado.

```bash
# Instalar dependencias
uv sync

# Configurar variables de entorno
cp .env.example .env
# completar ANTHROPIC_API_KEY y LANGSMITH_API_KEY en .env

# Correr el entrypoint
uv run python -m app.main
```

### Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `ENVIRONMENT` | `development` | Entorno de ejecución |
| `LANGSMITH_TRACING` | `false` | Activa tracing de LangChain en LangSmith |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` | Endpoint de LangSmith |
| `LANGSMITH_API_KEY` | *(requerida)* | API key de LangSmith |
| `LANGSMITH_PROJECT` | `SemanticProductSearch` | Proyecto en LangSmith |
| `ANTHROPIC_API_KEY` | *(requerida)* | API key de Anthropic (Claude) |
| `DATABASE_URL` | `sqlite:///./semantic_product_search.db` | Connection string de la base de datos |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Modelo de embeddings |
| `MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Modelo usado para similarity search |
| `TOP_K` | `5` | Cantidad de resultados a devolver por búsqueda |

> ⚠️ **Nunca loguees los valores de las API keys ni de ningún secreto**
> (`ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY`, etc.). Si necesitas debuggear
> `Settings`, imprime únicamente los nombres de los campos que fallaron, no
> sus valores — así lo hace `app/core/config.py` al validar al arranque.

## Roadmap

El desarrollo está organizado en fases (ver tablero de Notion):

1. Setup backend
2. Catálogo + embeddings
3. Búsqueda semántica
4. Reviews + comentarios
5. Servidor MCP
6. Agente + recomendación
7. REST API + streaming
8. Optimización
9. Frontend + publicación

## Arquitectura y decisiones de diseño

_Pendiente — se documenta en la Fase 9 (`PROD-32`), una vez el proyecto tenga
un flujo end-to-end para poder describir el diagrama, la demo y las
decisiones (caché, retrieval + re-ranking, etc.) con contexto real._
