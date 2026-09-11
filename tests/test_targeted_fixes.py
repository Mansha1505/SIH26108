import pytest
from backend.services.recommendation_service import RecommendationService
from backend.models.schemas import RecommendationRequest
from backend.retrieval.query_expansion import expand_procurement_query

@pytest.fixture(scope="module")
def service():
    srv = RecommendationService()
    srv.initialize()
    return srv


def test_query_expansion():
    hindi_query = "कृषि के लिए सबमर्सिबल पानी का पंप"
    expanded = expand_procurement_query(hindi_query)
    assert hindi_query in expanded
    assert "submersible" in expanded
    assert "water" in expanded
    assert "pump" in expanded
    assert "agriculture" in expanded


def test_result_count_filters(service):
    for k in [3, 5, 10]:
        req = RecommendationRequest(query="50W LED street light", top_k=k)
        resp = service.recommend(req)
        assert len(resp.recommendations) == min(k, resp.total_candidates)

    # Test top_k larger than corpus size
    req_large = RecommendationRequest(query="50W LED street light", top_k=50)
    resp_large = service.recommend(req_large)
    assert len(resp_large.recommendations) == resp_large.total_candidates


def test_english_retrieval_benchmarks(service):
    # 1. Transformer -> IS 1180
    resp_tx = service.recommend(RecommendationRequest(query="100kVA 11kV outdoor distribution transformer", top_k=5))
    assert resp_tx.recommendations[0].is_number.startswith("IS 1180")

    # 2. LED -> IS 10322
    resp_led = service.recommend(RecommendationRequest(query="50W LED street light for outdoor municipal roads", top_k=5))
    assert resp_led.recommendations[0].is_number.startswith("IS 10322")

    # 3. Cement -> IS 455
    resp_cem = service.recommend(RecommendationRequest(query="Portland Slag Cement for structural foundation work", top_k=5))
    assert resp_cem.recommendations[0].is_number.startswith("IS 455")

    # 4. Pump -> IS 12225
    resp_pump = service.recommend(RecommendationRequest(query="Submersible pump set for agricultural water supply", top_k=5))
    assert resp_pump.recommendations[0].is_number.startswith("IS 12225")


def test_hindi_retrieval_benchmarks(service):
    # 1. Hindi Pump -> IS 12225
    resp_h_pump = service.recommend(RecommendationRequest(query="कृषि के लिए सबमर्सिबल पानी का पंप", top_k=5))
    assert resp_h_pump.recommendations[0].is_number.startswith("IS 12225")

    # 2. Hindi LED -> IS 10322
    resp_h_led = service.recommend(RecommendationRequest(query="कृषि के लिए एलईडी स्ट्रीट लाइट", top_k=5))
    assert resp_h_led.recommendations[0].is_number.startswith("IS 10322")

    # 3. Hindi Cement -> IS 455
    resp_h_cem = service.recommend(RecommendationRequest(query="संरचनात्मक कार्य के लिए पोर्टलैंड स्लैग सीमेंट", top_k=5))
    assert resp_h_cem.recommendations[0].is_number.startswith("IS 455")


def test_hinglish_retrieval_benchmark(service):
    resp_hing = service.recommend(RecommendationRequest(query="kheti ke liye submersible water pump", top_k=5))
    assert resp_hing.recommendations[0].is_number.startswith("IS 12225")


def test_relative_match_score_calculation(service):
    resp = service.recommend(RecommendationRequest(query="50W LED street light", top_k=5))
    assert len(resp.recommendations) > 0
    top_rec = resp.recommendations[0]
    
    # Top item relative_match_score must be 100.0
    assert top_rec.relative_match_score == 100.0
    # Raw relevance score must still be present and preserved
    assert hasattr(top_rec, "relevance_score")
    assert top_rec.relevance_score > 0.0

    # Ensure second item relative_match_score <= 100.0
    if len(resp.recommendations) > 1:
        assert resp.recommendations[1].relative_match_score <= 100.0


def test_negative_query(service):
    resp_neg = service.recommend(RecommendationRequest(query="office chair for employees", top_k=5))
    assert len(resp_neg.recommendations) > 0
    # Negative query receives low/zero raw relevance score without false confidence
    top_neg = resp_neg.recommendations[0]
    assert top_neg.relevance_score < 0.5
    assert top_neg.relative_match_score == 0.0
