import os
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.retrieval.loader import get_default_repository
from scripts.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    mrr_at_k,
    ndcg_at_k
)

client = TestClient(app)

DATASET_PATH = os.path.abspath("scripts/evaluation_dataset.json")
BASELINE_PATH = os.path.abspath("scripts/evaluation_baseline.json")


def test_gold_dataset_integrity_and_validity():
    """Tests 1, 2 & 3: Gold dataset loads successfully and all standard IDs exist in corpus."""
    assert os.path.exists(DATASET_PATH), f"Gold dataset file missing: {DATASET_PATH}"
    
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        gold_dataset = json.load(f)

    assert len(gold_dataset) >= 15, "Gold dataset should contain at least 15 evaluation queries"

    repo = get_default_repository()
    standards = repo.get_all_standards()
    valid_std_ids = set(std["id"] for std in standards)

    for item in gold_dataset:
        assert "id" in item
        assert "query" in item and len(item["query"].strip()) > 0
        assert "language" in item and item["language"] in ["en", "hi", "hi-Latn"]
        assert "domain" in item
        assert "relevant_standard_ids" in item and len(item["relevant_standard_ids"]) > 0
        assert "relevance" in item and len(item["relevance"]) > 0

        # Verify every referenced standard ID exists in backend/data/standards.json
        for std_id in item["relevant_standard_ids"]:
            assert std_id in valid_std_ids, f"Standard ID '{std_id}' in query '{item['id']}' not found in standards.json"


def test_metric_precision_at_k_math():
    """Test 5: Mathematical correctness of Precision@K."""
    rel_map = {"IS-1180-P1": 2, "IS-2026-P1": 1}
    
    # 2 hits out of 3 retrieved -> P@3 = 2/3 = 0.6667
    retrieved = ["IS-1180-P1", "IS-2026-P1", "IS-4984"]
    p3 = precision_at_k(retrieved, rel_map, k=3)
    assert pytest.approx(p3, 0.001) == 0.6667

    # 1 hit out of 1 retrieved -> P@1 = 1.0
    p1 = precision_at_k(retrieved, rel_map, k=1)
    assert p1 == 1.0


def test_metric_recall_at_k_math():
    """Test 6: Mathematical correctness of Recall@K."""
    rel_map = {"IS-1180-P1": 2, "IS-2026-P1": 1}
    
    # 1 hit out of 2 ground truth relevant items -> R@1 = 0.5
    retrieved = ["IS-1180-P1", "IS-4984"]
    r1 = recall_at_k(retrieved, rel_map, k=1)
    assert r1 == 0.5

    # 2 hits out of 2 ground truth relevant items -> R@2 = 1.0
    retrieved_both = ["IS-1180-P1", "IS-2026-P1"]
    r2 = recall_at_k(retrieved_both, rel_map, k=2)
    assert r2 == 1.0


def test_metric_mrr_at_k_math():
    """Test 7: Mathematical correctness of Mean Reciprocal Rank (MRR)."""
    rel_map = {"IS-4984": 2}
    
    # First relevant hit at rank 2 -> MRR = 1/2 = 0.5
    retrieved = ["IS-1180-P1", "IS-4984", "IS-455"]
    mrr = mrr_at_k(retrieved, rel_map, k=3)
    assert mrr == 0.5

    # Relevant hit at rank 1 -> MRR = 1.0
    retrieved_top = ["IS-4984", "IS-1180-P1"]
    assert mrr_at_k(retrieved_top, rel_map, k=3) == 1.0


def test_metric_ndcg_at_k_math():
    """Test 8: Mathematical correctness of NDCG@K for graded relevance."""
    rel_map = {"IS-1180-P1": 2, "IS-2026-P1": 1}
    
    # Ideal ordering: IS-1180-P1 (rel 2), IS-2026-P1 (rel 1)
    # DCG = (2^2 - 1)/log2(2) + (2^1 - 1)/log2(3) = 3/1 + 1/1.58496 = 3 + 0.6309 = 3.6309
    # IDCG = 3.6309 -> NDCG = 1.0
    retrieved_ideal = ["IS-1180-P1", "IS-2026-P1"]
    ndcg_ideal = ndcg_at_k(retrieved_ideal, rel_map, k=2)
    assert pytest.approx(ndcg_ideal, 0.001) == 1.0

    # Reversed ordering: IS-2026-P1 (rel 1), IS-1180-P1 (rel 2)
    # DCG = (2^1 - 1)/log2(2) + (2^2 - 1)/log2(3) = 1/1 + 3/1.58496 = 1 + 1.8928 = 2.8928
    # NDCG = 2.8928 / 3.6309 = 0.7967
    retrieved_reversed = ["IS-2026-P1", "IS-1180-P1"]
    ndcg_rev = ndcg_at_k(retrieved_reversed, rel_map, k=2)
    assert pytest.approx(ndcg_rev, 0.001) == 0.7967


def test_retrieval_api_regression_gate():
    """Test 10 & 11: Verify existing APIs work and metric regression tolerance is satisfied."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    req_payload = {"query": "100 kVA three phase distribution transformer", "top_k": 5}
    rec_resp = client.post("/api/recommend", json=req_payload)
    assert rec_resp.status_code == 200
    assert len(rec_resp.json()["recommendations"]) == 5

    # Check evaluation baseline regression tolerance if baseline file exists
    if os.path.exists(BASELINE_PATH):
        with open(BASELINE_PATH, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)
        assert "baseline_metrics" in baseline_data
