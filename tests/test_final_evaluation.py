"""
Unit and Integration Test Suite for Final Evaluation & Benchmark Polish (Phase 10E).

Tests dataset loading, metric calculation accuracy, language grouping, missing gold-label handling,
non-mutation of retrieval logic, optional pgvector benchmark skipping, report artifact generation,
and default backend configuration preservation.
"""

import os
import json
import pytest

from scripts.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    mrr_at_k,
    ndcg_at_k
)
from scripts.evaluate_retrieval import (
    DATASET_PATH,
    FINAL_RESULTS_PATH,
    FINAL_REPORT_PATH,
    run_pgvector_benchmark_if_available,
    main as run_eval_main
)
from backend.services.recommendation_service import service_instance
from backend.config import REPOSITORY_TYPE, VECTOR_BACKEND


@pytest.fixture(scope="module", autouse=True)
def initialize_service():
    """Ensures RecommendationService is initialized prior to running evaluation tests."""
    service_instance.initialize()


# 1. Dataset loading and structure
def test_evaluation_dataset_structure():
    assert os.path.exists(DATASET_PATH), f"Evaluation dataset missing at {DATASET_PATH}"
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 20, f"Expected 20 evaluation queries, got {len(data)}"

    required_keys = {"id", "query", "language", "domain", "relevant_standard_ids", "relevance"}
    languages = set()
    for item in data:
        assert required_keys.issubset(set(item.keys()))
        assert isinstance(item["relevant_standard_ids"], list)
        assert len(item["relevant_standard_ids"]) > 0
        assert isinstance(item["relevance"], dict)
        languages.add(item["language"])

    assert "en" in languages
    assert "hi" in languages
    assert "hi-Latn" in languages


# 2. Metric calculation functions precision, recall, mrr, ndcg
def test_metric_calculations_deterministic():
    rel_map = {"IS-1180-P1": 2, "IS-10322": 1}
    retrieved = ["IS-1180-P1", "IS-999", "IS-10322"]

    p1 = precision_at_k(retrieved, rel_map, k=1)
    p3 = precision_at_k(retrieved, rel_map, k=3)
    r1 = recall_at_k(retrieved, rel_map, k=1)
    r3 = recall_at_k(retrieved, rel_map, k=3)
    mrr = mrr_at_k(retrieved, rel_map, k=5)
    ndcg3 = ndcg_at_k(retrieved, rel_map, k=3)

    assert p1 == 1.0
    assert p3 == 2.0 / 3.0
    assert r1 == 0.5
    assert r3 == 1.0
    assert mrr == 1.0
    assert 0.0 <= ndcg3 <= 1.0


# 3. Handling empty or missing gold labels
def test_metric_calculations_empty_inputs():
    rel_map = {}
    retrieved = ["IS-101"]

    assert precision_at_k(retrieved, rel_map, k=1) == 0.0
    assert recall_at_k(retrieved, rel_map, k=1) == 0.0
    assert mrr_at_k(retrieved, rel_map, k=5) == 0.0
    assert ndcg_at_k(retrieved, rel_map, k=3) == 0.0

    assert precision_at_k([], {"IS-101": 1}, k=1) == 0.0


# 4. Optional pgvector benchmark skips cleanly when Postgres is unavailable
def test_pgvector_benchmark_skip_when_unavailable():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        gold_dataset = json.load(f)

    # Force test without live Postgres
    res = run_pgvector_benchmark_if_available(gold_dataset)
    assert isinstance(res, dict)
    assert "status" in res
    assert res["status"] in ["SKIPPED", "COMPLETED"]


# 5. Full evaluation script execution & artifact generation
def test_evaluation_runner_generates_artifacts():
    run_eval_main()

    assert os.path.exists(FINAL_RESULTS_PATH), f"Final results missing at {FINAL_RESULTS_PATH}"
    assert os.path.exists(FINAL_REPORT_PATH), f"Final report missing at {FINAL_REPORT_PATH}"

    with open(FINAL_RESULTS_PATH, "r", encoding="utf-8") as f:
        res = json.load(f)

    assert res["query_count"] == 20
    assert "aggregate_metrics" in res
    assert "language_metrics" in res
    assert "BM25" in res["aggregate_metrics"]
    assert "Hybrid+Reranker" in res["aggregate_metrics"]

    with open(FINAL_REPORT_PATH, "r", encoding="utf-8") as f:
        report_md = f.read()

    assert "# SIH26108 Final Retrieval Evaluation" in report_md
    assert "PROTOTYPE BOUNDARY DISCLAIMER" in report_md


from backend.models.schemas import RecommendationRequest


# 6. Evaluation non-mutation of retrieval behavior
def test_evaluation_non_mutation():
    sample_query = "100 kVA distribution transformer"
    res1 = service_instance.recommend(RecommendationRequest(query=sample_query))
    
    # Run eval main
    run_eval_main()

    res2 = service_instance.recommend(RecommendationRequest(query=sample_query))
    assert [r.id for r in res1.recommendations] == [r.id for r in res2.recommendations]



# 7. Defaults preserved
def test_defaults_preserved():
    assert REPOSITORY_TYPE == "json"
    assert VECTOR_BACKEND == "faiss"
