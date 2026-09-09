"""
Unit and Integration Tests for pgvector Foundation (Phase 10B - Chunk 1).

Tests pgvector dependency availability, configuration defaults, non-blocking extension check,
SQLAlchemy Vector type instantiation without live database, and vector configuration isolation.
"""

import os
import pytest
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base

from backend.config import VECTOR_BACKEND, REPOSITORY_TYPE
from backend.database.vector import (
    Vector,
    is_pgvector_package_available,
    get_active_vector_backend,
    check_pgvector_extension
)
from backend.database.connection import check_database_connection
from backend.retrieval.embeddings import SemanticEmbeddingEngine
from backend.services.recommendation_service import service_instance


def test_pgvector_python_package_available():
    """1: Verifies that the pgvector Python package is installed and importable."""
    assert is_pgvector_package_available() is True
    assert Vector is not None


def test_vector_backend_configuration_defaults_to_faiss(monkeypatch):
    """2: Verifies that VECTOR_BACKEND configuration defaults to 'faiss'."""
    monkeypatch.delenv("VECTOR_BACKEND", raising=False)
    assert get_active_vector_backend() == "faiss"
    assert VECTOR_BACKEND == "faiss"


def test_vector_backend_configuration_can_be_overridden(monkeypatch):
    """3: Verifies that VECTOR_BACKEND environment variable can be overridden to 'pgvector'."""
    monkeypatch.setenv("VECTOR_BACKEND", "pgvector")
    assert get_active_vector_backend() == "pgvector"


def test_vector_infrastructure_import_does_not_require_postgresql():
    """4 & 5: Verifies importing vector infrastructure and app modules does not require an active PostgreSQL connection."""
    # Module imports succeeded without active connection
    assert Vector is not None
    assert service_instance is not None


def test_check_pgvector_extension_graceful_failure_when_db_unavailable():
    """6: Verifies check_pgvector_extension fails gracefully with structured dictionary when DB is unreachable."""
    try:
        bad_engine = create_engine("postgresql+psycopg://postgres:invalid@localhost:59999/nonexistent", connect_args={"connect_timeout": 1})
        res = check_pgvector_extension(engine=bad_engine)
        assert isinstance(res, dict)
        assert res["postgres_available"] is False
        assert res["pgvector_available"] is False
    except (ImportError, ModuleNotFoundError):
        # Driver missing
        bad_engine = create_engine("sqlite:////non_existent_directory_xyz/invalid.db")
        res = check_pgvector_extension(engine=bad_engine)
        assert isinstance(res, dict)
        assert res["postgres_available"] is False


def test_vector_sqlalchemy_type_instantiation_without_live_db():
    """9: Verifies pgvector SQLAlchemy Vector type can be instantiated and configured without requiring a live Postgres connection."""
    if not is_pgvector_package_available():
        pytest.skip("pgvector Python package not installed")

    # Instantiate SQLAlchemy Vector column type with dimension 384 (MiniLM) and 1024 (BGE-M3)
    vec_384 = Vector(384)
    vec_1024 = Vector(1024)

    assert vec_384.dim == 384
    assert vec_1024.dim == 1024

    # Verify model definition containing Vector column compiles under SQLAlchemy DeclarativeBase
    BaseTest = declarative_base()

    class TestVectorModel(BaseTest):
        __tablename__ = "test_vector_table"
        id = Column(Integer, primary_key=True)
        embedding = Column(Vector(384))

    assert TestVectorModel.__tablename__ == "test_vector_table"


def test_faiss_dense_retrieval_baseline_unaffected():
    """7 & 8: Verifies that adding vector foundation does not alter FAISS default or existing embedding retrieval."""
    sample_standards = [
        {
            "id": "IS-TEST-1",
            "is_number": "IS TEST 1",
            "title": "LED Street Lighting Luminaire",
            "scope": "LED luminaires for outdoor road street lighting",
            "sector": "Electrotechnical",
            "product_category": "Lighting",
            "keywords": ["LED", "lighting"],
            "revision_year": 2020,
            "status": "Active (DEMO / SAMPLE DATA)",
            "source_url": None,
            "description": "Test fixture",
            "amendments": [],
            "related_standards": []
        }
    ]

    engine = SemanticEmbeddingEngine(sample_standards)
    assert engine.doc_embeddings is not None  # Dense doc embeddings initialized
    scores = engine.search("LED street light")
    assert len(scores) == 1
    assert scores[0][0] == 0  # index 0 matches IS-TEST-1
    assert scores[0][1] > 0.0



@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "true",
    reason="Live PostgreSQL pgvector capability test skipped because RUN_POSTGRES_TESTS != 'true'"
)
def test_live_postgresql_pgvector_extension_capability():
    """10: Optional live PostgreSQL capability test running only when RUN_POSTGRES_TESTS='true'."""
    postgres_url = os.getenv("POSTGRES_TEST_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sih26108_standards")
    engine = create_engine(postgres_url)
    
    if not check_database_connection(engine):
        pytest.skip("PostgreSQL server is unreachable at POSTGRES_TEST_URL")

    res = check_pgvector_extension(engine=engine)
    assert res["postgres_available"] is True
    # Log result details for test output
    print(f"\nLive PostgreSQL pgvector capability check result: {res}")
