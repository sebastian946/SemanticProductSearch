"""Evaluación de retrieval en LangSmith: dataset + evaluator (PROD-36).

Sube el eval set local como dataset de LangSmith (idempotente) y corre la
evaluación con un evaluator de recall@k. Los resultados quedan visibles en
el dashboard de LangSmith, comparables entre corridas.

    uv run python -m tests.eval_langsmith
"""

import json
import os
from pathlib import Path

from app.core.config import settings

os.environ.setdefault(
    "LANGSMITH_API_KEY", settings.langsmith_api_key.get_secret_value()
)
os.environ.setdefault("LANGSMITH_ENDPOINT", settings.langsmith_endpoint)

from langsmith import Client  # noqa: E402

from app.search.semantic_search import search  # noqa: E402

DATASET_NAME = "semantic-product-search-retrieval"
EVAL_SET_PATH = Path(__file__).parent / "retrieval_eval_set.json"
TOP_K = 5


def sync_dataset(client: Client):
    cases = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))
    if client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Queries con productos esperados para recall@k",
        )
        client.create_examples(
            inputs=[{"query": case["query"]} for case in cases],
            outputs=[{"expected_ids": case["expected_ids"]} for case in cases],
            dataset_id=dataset.id,
        )
    return dataset


def run_search(inputs: dict) -> dict:
    results = search(inputs["query"], top_k=TOP_K)
    return {"found_ids": [row["id"] for row in results]}


def recall_at_k(outputs: dict, reference_outputs: dict) -> bool:
    found = outputs["found_ids"]
    return any(pid in found for pid in reference_outputs["expected_ids"])


if __name__ == "__main__":
    client = Client()
    sync_dataset(client)
    experiment = client.evaluate(
        run_search,
        data=DATASET_NAME,
        evaluators=[recall_at_k],
        experiment_prefix="retrieval-recall",
    )
    print(f"experimento: {experiment.experiment_name}")
