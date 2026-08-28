# Servidor MCP — semantic-product-search

Servidor MCP (SDK `mcp` 2.x, transporte stdio) que expone la búsqueda
semántica y las reviews del proyecto.

## Tools

- `search_products(query, top_k, category, brand, min_price, max_price)` —
  búsqueda semántica multilingüe con filtros de metadata.
- `get_reviews(product_id)` — reseñas de un producto.
- `add_review(product_id, rating, comment, language)` — agrega una reseña
  (valida rating 1-5, comment no vacío, producto existente).

## Resources

- `catalog://products` — catálogo completo (id, título, categoría, marca, precio).

## Correrlo local

```bash
uv run python -m app.mcp_server.server
```

Requiere Postgres+pgvector arriba (`docker compose up -d`) y el catálogo
ingerido (`uv run python -m app.search.embedder`).

## Probarlo desde Claude Desktop (PROD-20)

Agregar a `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "semantic-product-search": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server.server"],
      "cwd": "c:/repositories/SemanticProductSearch"
    }
  }
}
```

Reiniciar Claude Desktop y pedirle por ejemplo: "buscá algo para mantener
el café caliente y mostrame sus reseñas".
