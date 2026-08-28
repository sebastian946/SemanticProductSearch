"""Agente recomendador que consume el servidor MCP del proyecto (PROD-21..24).

Decisiones documentadas:

- Multilingüe (PROD-22): estrategia A — se confía en el embedding multilingüe
  (el match ya funciona cross-idioma, probado en PROD-10), así que el query
  del usuario se pasa tal cual a search_products, sin servicio de traducción
  aparte. El LLM responde en el idioma del usuario vía system prompt.

- Recomendación (PROD-23): esto es retrieval + re-ranking con LLM, no
  collaborative filtering. El LLM recibe los top-K reales (specs, precio,
  reviews vía tools MCP) y justifica citando esos datos.

- LLM: usa Anthropic si hay ANTHROPIC_API_KEY real en el entorno; si no,
  cae a Ollama local (llama3.2) para poder desarrollar sin costo.

- MCP externo (PROD-24): además del servidor propio se monta
  `mcp-server-fetch` (servidor de referencia oficial), que permite al agente
  traer el contenido de un product_url si necesita más contexto.
"""

import asyncio

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.config import settings

PROJECT_DIR = "c:/repositories/SemanticProductSearch"

MCP_SERVERS = {
    "semantic-product-search": {
        "transport": "stdio",
        "command": "uv",
        "args": ["run", "python", "-m", "app.mcp_server.server"],
        "cwd": PROJECT_DIR,
    },
    "fetch": {
        "transport": "stdio",
        "command": "uvx",
        "args": ["mcp-server-fetch"],
    },
}

SYSTEM_PROMPT = """\
Eres un asistente de compras. Tienes tools para buscar productos por
significado (search_products), leer reseñas (get_reviews), agregar reseñas
(add_review) y traer contenido de una URL (fetch).

Cuando el usuario describe lo que necesita:
1. Llama a search_products con su query TAL CUAL lo escribió (la búsqueda es
   multilingüe, no traduzcas el query).
2. Si hay resultados, consulta get_reviews del mejor candidato.
3. Recomienda UN producto y justifica con datos reales de los resultados
   (título, precio, score, reseñas). No inventes características.
4. Responde SIEMPRE en el idioma en que escribió el usuario.
"""


def _build_llm():
    api_key = settings.anthropic_api_key.get_secret_value()
    if api_key and not api_key.startswith("<"):
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model="claude-sonnet-5", max_tokens=1024)

    from langchain_ollama import ChatOllama

    return ChatOllama(model="llama3.2")


async def recommend(user_query: str) -> dict:
    client = MultiServerMCPClient(MCP_SERVERS)
    tools = await client.get_tools()

    agent = create_agent(_build_llm(), tools, system_prompt=SYSTEM_PROMPT)
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_query}]}
    )

    messages = result["messages"]
    tool_calls = [
        call["name"]
        for message in messages
        for call in getattr(message, "tool_calls", None) or []
    ]
    return {"answer": messages[-1].content, "tool_calls": tool_calls}


async def stream_recommendation(user_query: str):
    """Genera la recomendación token a token (para SSE)."""
    client = MultiServerMCPClient(MCP_SERVERS)
    tools = await client.get_tools()

    agent = create_agent(_build_llm(), tools, system_prompt=SYSTEM_PROMPT)
    async for chunk, _metadata in agent.astream(
        {"messages": [{"role": "user", "content": user_query}]},
        stream_mode="messages",
    ):
        content = getattr(chunk, "content", "")
        if isinstance(content, str) and content and not getattr(
            chunk, "tool_call_id", None
        ):
            yield content


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "algo para mantener el café caliente"
    outcome = asyncio.run(recommend(query))
    print("tools usadas:", outcome["tool_calls"])
    print()
    print(outcome["answer"])
