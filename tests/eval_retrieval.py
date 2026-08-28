"""Evaluación de retrieval: recall@k sobre un set versionado (PROD-31).

Un caso cuenta como acierto si ALGUNO de sus expected_ids aparece en el
top-K. Correr con la DB arriba y el catálogo ingerido:

    uv run python -m tests.eval_retrieval [k]
"""

import json
import sys
from pathlib import Path

from app.search.semantic_search import search

EVAL_SET_PATH = Path(__file__).parent / "retrieval_eval_set.json"


def evaluate(k: int = 5) -> float:
    cases = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))
    hits = 0

    print(f"recall@{k} sobre {len(cases)} queries\n")
    for case in cases:
        results = search(case["query"], top_k=k)
        found_ids = [row["id"] for row in results]
        hit = any(pid in found_ids for pid in case["expected_ids"])
        hits += hit
        mark = "OK " if hit else "MISS"
        print(f"  [{mark}] {case['query']!r}")
        if not hit:
            top = [(row["id"], row["title"]) for row in results[:3]]
            print(f"         esperaba {case['expected_ids']}, top-3: {top}")

    recall = hits / len(cases)
    print(f"\nrecall@{k} = {hits}/{len(cases)} = {recall:.2%}")
    return recall


if __name__ == "__main__":
    top_k = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    evaluate(top_k)
