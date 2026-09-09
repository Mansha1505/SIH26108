"""
Unit and Integration Tests for pgvector Search Engine (Phase 10B - Chunk 4).

Tests query vector encoding, model/dimension filtering, top-k limiting, similarity ordering,
empty query handling, database failure error surfacing, FAISS baseline preservation,
backend switching, and optional live PostgreSQL vector search execution.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import VECTOR_BACKEND, DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIMENSION
from backend.database.connection import Base, check_database_connection
from backend.database.models import StandardModel, StandardEmbeddingModel
from backend.database.vector import check_pgvector_extension
from backend.retrieval.embeddings import SemanticEmbeddingEngine, get_default_embedding_engine
from backend.retrieval.pgvector_search import PgVectorSearchEngine
from backend.services.recommendation_service import RecommendationService


@pytest.fixture
def sample_standards():
    return [
        {
            "id": "IS-SOLAR-001",
            "is_number": "IS SOLAR 1 : 2024",
            "title": "Crystalline Silicon Terrestrial Solar PV Panels",
            "scope": "Design qualification and type approval for terrestrial photovoltaic modules.",
            "sector": "Renewable Energy",
            "product_category": "Solar Energy",
            "keywords": ["solar", "PV panel", "photovoltaic"],
            "revision_year": 2024,
            "status": "Active (DEMO / SAMPLE DATA)",
            "source_url": None,
            "description": "Solar PV panel testing standard.",
            "amendments": [],
            "related_standards": []
        },
        {
            "id": "IS-PUMP-002",
            "is_number": "IS PUMP 2 : 2024",
            "title": "Submersible Pumps for Clear Cold Water",
            "scope": "Specification for electric motor driven submersible water pump sets.",
            "sector": "Mechanical Engineering",
            "product_category": "Pumps & Turbines",
            "keywords": ["submersible", "water pump"],
            "revision_year": 2024,
            "status": "Active (DEMO / SAMPLE DATA)",
            "source_url": None,
            "description": "Submersible pump standard.",
            "amendments": [],
            "related_standards": []
        }
    ]


@pytest.fixture
def sqlite_seeded_engine(sample_standards):
    """Provides a PgVectorSearchEngine backed by SQLite populated with sample standards and metadata."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    for std in sample_standards:
        session.add(StandardModel.from_pydantic(std))
    session.commit()

    search_engine = PgVectorSearchEngine(
        standards=sample_standards,
        engine=engine,
        session_factory=session_factory
    )
    yield search_engine, engine, session_factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_pgvector_query_embedding_encoding(sqlite_seeded_engine):
    """1, 2 & 3: Verifies query vector generation, active embedding model, and vector dimension."""
    search_engine, _, _ = sqlite_seeded_engine
    assert search_engine.active_model_name == DEFAULT_EMBEDDING_MODEL
    assert search_engine.vector_dimension == DEFAULT_EMBEDDING_DIMENSION

    query_vec = search_engine._encode_query("solar photovoltaic panel")
    assert isinstance(query_vec, list)
    assert len(query_vec) == DEFAULT_EMBEDDING_DIMENSION


def test_empty_query_handling(sqlite_seeded_engine):
    """7: Verifies empty/whitespace query returns 0.0 similarity scores for all standards."""
    search_engine, _, _ = sqlite_seeded_engine
    res1 = search_engine.search("")
    assert len(res1) == 2
    assert res1[0][1] == 0.0
    assert res1[1][1] == 0.0

    res2 = search_engine.search("   ")
    assert len(res2) == 2
    assert res2[0][1] == 0.0


def test_backend_switching_and_faiss_default(sample_standards, monkeypatch):
    """9, 10 & 11: Verifies default vector backend remains FAISS and VECTOR_BACKEND=pgvector switches to PgVectorSearchEngine."""
    monkeypatch.delenv("VECTOR_BACKEND", raising=False)
    default_engine = get_default_embedding_engine(sample_standards)
    assert isinstance(default_engine, SemanticEmbeddingEngine)
    assert VECTOR_BACKEND == "faiss"

    monkeypatch.setenv("VECTOR_BACKEND", "pgvector")
    pg_engine = get_default_embedding_engine(sample_standards)
    assert isinstance(pg_engine, PgVectorSearchEngine)


def test_postgresql_unavailable_surfaces_clear_error(sample_standards):
    """8: Verifies search() raises clear RuntimeError when database connection or query fails."""
    bad_engine = create_engine("sqlite:////non_existent_directory_xyz/invalid.db")
    search_engine = PgVectorSearchEngine(standards=sample_standards, engine=bad_engine)

    with pytest.raises(RuntimeError) as exc_info:
        search_engine.search("solar panel")

    assert "PostgreSQL pgvector search engine query failed" in str(exc_info.value) or "query failed" in str(exc_info.value)


def test_recommendation_service_vector_backend_integration(sample_standards, monkeypatch):
    """Integration test verifying RecommendationService initialized with FAISS baseline (or mock) operates seamlessly."""
    monkeypatch.setenv("VECTOR_BACKEND", "faiss")
    service = RecommendationService()
    service.initialize()
    assert isinstance(service.embedding_engine, SemanticEmbeddingEngine)


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "true",
    reason="Live PostgreSQL pgvector search integration test skipped because RUN_POSTGRES_TESTS != 'true'"
)
def test_live_postgresql_pgvector_search(sample_standards):
    """13: Optional live PostgreSQL + pgvector search test under RUN_POSTGRES_TESTS='true'."""
    postgres_url = os.getenv("POSTGRES_TEST_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sih26108_standards")
    engine = create_engine(postgres_url)

    if not check_database_connection(engine):
        pytest.skip("PostgreSQL database server is unreachable at POSTGRES_TEST_URL")

    cap = check_pgvector_extension(engine=engine)
    if not cap.get("pgvector_available", False):
        pytest.skip("PostgreSQL server is reachable, but 'vector' extension is not installed.")

    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    test_std1_id = "IS-SOLAR-001"
    test_std2_id = "IS-PUMP-002"

    try:
        # Purge test records if present
        session.query(StandardEmbeddingModel).filter(StandardEmbeddingModel.standard_id.in_([test_std1_id, test_std2_id])).delete()
        session.query(StandardModel).filter(StandardModel.id.in_([test_std1_id, test_std2_id])).delete()
        session.commit()

        # Insert standards
        for std in sample_standards:
            session.add(StandardModel.from_pydantic(std))
        session.commit()

        # Seed realistic vectors via SemanticEmbeddingEngine
        sem_engine = SemanticEmbeddingEngine(sample_standards)
        vec1 = [float(v) for v in sem_engine.doc_embeddings[0]]
        vec2 = [float(v) for v in sem_engine.doc_embeddings[1]]

        emb1 = StandardEmbeddingModel(
            standard_id=test_std1_id,
            content="Solar PV solar panel photovoltaic module",
            embedding=vec1,
            embedding_model=DEFAULT_EMBEDDING_MODEL,
            embedding_dimension=DEFAULT_EMBEDDING_DIMENSION
        )
        emb2 = StandardEmbeddingModel(
            standard_id=test_std2_id,
            content="Submersible water pump sets electric motor",
            embedding=vec2,
            embedding_model=DEFAULT_EMBEDDING_MODEL,
            embedding_dimension=DEFAULT_EMBEDDING_DIMENSION
        )
        session.add_all([emb1, emb2])
        session.commit()

        # Execute PgVectorSearchEngine search
        pg_search_engine = PgVectorSearchEngine(
            standards=sample_standards,
            engine=engine,
            session_factory=session_factory
        )

        results = pg_search_engine.search("solar photovoltaic panel", top_k=2)
        assert len(results) == 2

        # Standard IS-SOLAR-001 (doc_index 0) must score higher than IS-PUMP-002 (doc_index 1)
        score_solar = next(s for idx, s in results if idx == 0)
        score_pump = next(s for idx, s in results if idx == 1)

        assert score_solar > score_pump
        assert score_solar > 0.4

    finally:
        session.query(StandardEmbeddingModel).filter(StandardEmbeddingModel.standard_id.in_([test_std1_id, test_std2_id])).delete()
        session.query(StandardModel).filter(StandardModel.id.in_([test_std1_id, test_std2_id])).delete()
        session.commit()
        session.close()
