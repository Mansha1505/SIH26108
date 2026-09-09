import pytest
from backend.retrieval.loader import JsonStandardsRepository, get_default_repository
from backend.retrieval.text_prep import tokenize_text, normalize_text
from backend.retrieval.bm25 import BM25SearchEngine
from backend.retrieval.hybrid import min_max_normalize
from backend.retrieval.ranking import CandidateRanker

def test_standards_repository():
    repo = get_default_repository()
    standards = repo.get_all_standards()
    assert len(standards) > 0
    
    # Test record fields and DEMO flag
    for std in standards:
        assert "DEMO" in std["status"]
        assert "id" in std
        assert "is_number" in std
        assert "title" in std
        assert "scope" in std
        assert "amendments" in std
        assert "related_standards" in std

def test_repository_lookup_by_id_and_is_number():
    repo = JsonStandardsRepository()
    standards = repo.get_all_standards()
    first_std = standards[0]
    
    # Test get_standard_by_id
    by_id = repo.get_standard_by_id(first_std["id"])
    assert by_id is not None
    assert by_id["is_number"] == first_std["is_number"]
    
    # Test get_standard_by_is_number
    by_is_num = repo.get_standard_by_is_number(first_std["is_number"])
    assert by_is_num is not None
    assert by_is_num["id"] == first_std["id"]

def test_text_prep():
    text = "50W LED Street Light for Municipal Roads!"
    norm = normalize_text(text)
    assert "50w" in norm
    assert "street" in norm
    tokens = tokenize_text(text)
    assert "50w" in tokens
    assert "led" in tokens

def test_bm25_search():
    repo = get_default_repository()
    standards = repo.get_all_standards()
    bm25 = BM25SearchEngine(standards)
    
    results = bm25.search("LED street light luminaire")
    assert len(results) == len(standards)
    
    sorted_res = sorted(results, key=lambda x: x[1], reverse=True)
    top_idx = sorted_res[0][0]
    top_std = standards[top_idx]
    assert "LED" in top_std["title"] or "Luminaire" in top_std["title"] or "10322" in top_std["is_number"]

def test_min_max_normalize():
    scores = [10.0, 20.0, 30.0, 40.0, 50.0]
    norm = min_max_normalize(scores)
    assert norm == [0.0, 0.25, 0.5, 0.75, 1.0]

def test_ranking_and_reasons():
    repo = get_default_repository()
    standards = repo.get_all_standards()
    ranker = CandidateRanker(standards)
    
    mock_candidates = [
        {
            "doc_index": 0,
            "bm25_raw": 5.0,
            "bm25_norm": 0.9,
            "semantic_raw": 0.85,
            "semantic_norm": 0.95,
            "relevance_score": 0.92
        }
    ]
    
    res = ranker.rerank_and_explain(
        query="50W LED street light",
        candidates=mock_candidates,
        top_k=1
    )
    
    assert len(res) == 1
    top_item = res[0]
    assert top_item["relevance_score"] == 0.92
    assert isinstance(top_item["reasons"], list)
    assert len(top_item["reasons"]) > 0
    assert "id" in top_item
    assert "amendments" in top_item
    assert "related_standards" in top_item
