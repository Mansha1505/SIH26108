"""
Unit and Integration Tests for Repository Switching & Application Integration (Phase 10A - Chunk 4).

Tests repository factory behavior, configuration overrides, equivalence of JSON and PostgreSQL
records, RecommendationService integration without database leak, and database failure handling.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.connection import Base, check_database_connection
from backend.database.seed import seed_standards, load_standards_from_json
from backend.retrieval.loader import (
    StandardsRepository,
    JsonStandardsRepository,
    PostgresStandardsRepository,
    get_default_repository
)
from backend.services.recommendation_service import RecommendationService
from backend.models.schemas import IndianStandardRecord


@pytest.fixture
def sqlite_seeded_repo():
    """Provides a PostgresStandardsRepository backed by an in-memory SQLite database populated with the test standards corpus."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Seed in-memory DB
    seed_standards(engine=engine, session_factory=session_factory)

    repo = PostgresStandardsRepository(session_factory=session_factory, engine=engine)
    yield repo

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_repository_factory_default_behavior(monkeypatch):
    """A & H: Verifies that without override, get_default_repository() returns JsonStandardsRepository."""
    monkeypatch.delenv("REPOSITORY_TYPE", raising=False)
    repo = get_default_repository()
    assert isinstance(repo, JsonStandardsRepository)


def test_repository_factory_explicit_json(monkeypatch):
    """B: Verifies REPOSITORY_TYPE=json explicitly returns JsonStandardsRepository."""
    monkeypatch.setenv("REPOSITORY_TYPE", "json")
    repo = get_default_repository()
    assert isinstance(repo, JsonStandardsRepository)


def test_repository_factory_explicit_postgres(monkeypatch):
    """C: Verifies REPOSITORY_TYPE=postgres explicitly returns PostgresStandardsRepository."""
    monkeypatch.setenv("REPOSITORY_TYPE", "postgres")
    repo = get_default_repository()
    assert isinstance(repo, PostgresStandardsRepository)


def test_repository_factory_explicit_parameter_override():
    """Verifies passing explicit parameter to get_default_repository() overrides environment."""
    repo_pg = get_default_repository(repository_type="postgres")
    assert isinstance(repo_pg, PostgresStandardsRepository)

    repo_json = get_default_repository(repository_type="json")
    assert isinstance(repo_json, JsonStandardsRepository)


def test_postgres_repository_retrieves_seeded_records(sqlite_seeded_repo):
    """D: Verifies PostgresStandardsRepository can retrieve seeded records from test database."""
    records = sqlite_seeded_repo.get_all_standards()
    assert len(records) == 14

    single_rec = sqlite_seeded_repo.get_standard_by_id("IS-10322-P5-S3")
    assert single_rec is not None
    assert single_rec["id"] == "IS-10322-P5-S3"

    by_is_no = sqlite_seeded_repo.get_standard_by_is_number("IS 10322 (Part 5/Sec 3) : 2012")
    assert by_is_no is not None
    assert by_is_no["id"] == "IS-10322-P5-S3"


def test_json_and_postgres_repository_equivalence(sqlite_seeded_repo):
    """E & 7: Integration-style comparison proving JSON and PostgreSQL repositories return equivalent records."""
    json_repo = JsonStandardsRepository()

    # 1. get_all_standards equivalence
    json_all = json_repo.get_all_standards()
    pg_all = sqlite_seeded_repo.get_all_standards()

    assert len(json_all) == len(pg_all)

    # Sort both by ID for deterministic comparison
    json_all_sorted = sorted(json_all, key=lambda x: x["id"])
    pg_all_sorted = sorted(pg_all, key=lambda x: x["id"])

    meaningful_fields = [
        "id", "is_number", "title", "scope", "sector", "product_category",
        "keywords", "revision_year", "status", "source_url", "description",
        "amendments", "related_standards"
    ]

    for j_rec, p_rec in zip(json_all_sorted, pg_all_sorted):
        # Validate into Pydantic models
        j_pydantic = IndianStandardRecord(**j_rec)
        p_pydantic = IndianStandardRecord(**p_rec)

        for field in meaningful_fields:
            assert getattr(j_pydantic, field) == getattr(p_pydantic, field), f"Mismatch in field '{field}' for standard '{j_rec['id']}'"

    # 2. get_standard_by_id equivalence
    test_id = "IS-16102-P1"
    j_single = json_repo.get_standard_by_id(test_id)
    p_single = sqlite_seeded_repo.get_standard_by_id(test_id)

    assert j_single is not None and p_single is not None
    assert IndianStandardRecord(**j_single) == IndianStandardRecord(**p_single)

    # 3. get_standard_by_is_number equivalence
    test_is = "IS 16102 (Part 1) : 2012"
    j_is = json_repo.get_standard_by_is_number(test_is)
    p_is = sqlite_seeded_repo.get_standard_by_is_number(test_is)

    assert j_is is not None and p_is is not None
    assert IndianStandardRecord(**j_is) == IndianStandardRecord(**p_is)


def test_recommendation_service_with_postgres_repository(sqlite_seeded_repo):
    """F: Verifies RecommendationService initializes and operates using PostgresStandardsRepository without DB leak."""
    service = RecommendationService(repository=sqlite_seeded_repo)
    service.initialize()

    assert service._is_initialized
    assert len(service.standards) == 14
    assert service.bm25_engine is not None
    assert service.embedding_engine is not None
    assert service.hybrid_retriever is not None
    assert service.graph_builder._is_built

    # Execute a sample recommendation query
    from backend.models.schemas import RecommendationRequest
    req = RecommendationRequest(query="LED street light 50W", top_k=3)
    resp = service.recommend(req)

    assert resp is not None
    assert len(resp.recommendations) > 0
    assert resp.total_candidates == 14


def test_postgres_connection_failure_surfaced_clearly():
    """G: Verifies clear error raising when PostgreSQL connection/query fails."""
    try:
        bad_engine = create_engine("postgresql+psycopg://postgres:invalid@localhost:59999/nonexistent_db", connect_args={"connect_timeout": 1})
        bad_repo = PostgresStandardsRepository(engine=bad_engine)
        with pytest.raises(RuntimeError) as exc_info:
            bad_repo.get_all_standards()
        assert "Failed to retrieve standards from PostgreSQL repository" in str(exc_info.value)
    except (ImportError, ModuleNotFoundError):
        # Driver missing - verify repository operation raises RuntimeError on invalid DB connection
        bad_engine = create_engine("sqlite:////non_existent_directory_xyz/invalid.db")
        bad_repo = PostgresStandardsRepository(engine=bad_engine)
        with pytest.raises(RuntimeError):
            bad_repo.get_all_standards()



@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "true",
    reason="Live PostgreSQL integration test skipped because RUN_POSTGRES_TESTS != 'true'"
)
def test_live_postgresql_repository_switching():
    """Live PostgreSQL repository switching test (skipped when RUN_POSTGRES_TESTS != 'true')."""
    postgres_url = os.getenv("POSTGRES_TEST_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sih26108_test")
    engine = create_engine(postgres_url)
    if not check_database_connection(engine):
        pytest.skip("PostgreSQL database server is unreachable at POSTGRES_TEST_URL")

    # Seed live test DB
    seed_standards(engine=engine)

    repo = PostgresStandardsRepository(engine=engine)
    service = RecommendationService(repository=repo)
    service.initialize()

    assert service._is_initialized
    assert len(service.standards) >= 14
