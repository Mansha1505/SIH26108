"""
Unit and Integration Tests for Embedding Population / Seed Utility (Phase 10B - Chunk 3).

Tests embedding content construction, SemanticEmbeddingEngine reuse, vector dimension validation,
metadata preservation, multi-standard population, malformed/empty content handling, idempotency,
unreachable database error handling, FAISS default baseline, and optional live PostgreSQL vector seeding.
"""

import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import VECTOR_BACKEND, DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIMENSION
from backend.database.connection import Base, check_database_connection
from backend.database.models import StandardModel, StandardEmbeddingModel
from backend.database.seed_embeddings import (
    build_embedding_content,
    seed_embeddings,
    main
)
from backend.database.vector import check_pgvector_extension
from backend.retrieval.embeddings import SemanticEmbeddingEngine


@pytest.fixture
def sqlite_db():
    """Provides an isolated SQLite in-memory engine and session factory for schema testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield engine, session_factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_build_embedding_content_construction():
    """1: Verifies correct embedding text content construction from standard fields."""
    sample_std = {
        "id": "IS-10322-P5-S3",
        "is_number": "IS 10322 (Part 5/Sec 3) : 2012",
        "title": "Luminaires for Road and Street Lighting",
        "scope": "Specifies safety and performance requirements for road lighting.",
        "sector": "Electrotechnical",
        "product_category": "Lighting & Luminaires",
        "keywords": ["LED", "street light", "road lighting"],
        "description": "Primary standard for municipal and highway street lighting."
    }

    content = build_embedding_content(sample_std)
    assert "IS 10322 (Part 5/Sec 3) : 2012" in content
    assert "Luminaires for Road and Street Lighting" in content
    assert "Electrotechnical" in content
    assert "Lighting & Luminaires" in content
    assert "LED street light road lighting" in content
    assert "Primary standard for municipal and highway street lighting." in content

    # Empty or non-dict input
    assert build_embedding_content({}) == ""
    assert build_embedding_content(None) == ""


def test_seed_embeddings_uses_existing_engine_and_metadata(sqlite_db):
    """2, 3, 4 & 5: Verifies embedding generation using SemanticEmbeddingEngine, metadata, and multi-standard population."""
    engine, session_factory = sqlite_db

    sample_standards = [
        {
            "id": "IS-SEED-001",
            "is_number": "IS SEED 1 : 2024",
            "title": "Solar Photovoltaic Module Specification",
            "scope": "Design qualification for crystalline silicon solar PV panels.",
            "sector": "Renewable Energy",
            "product_category": "Solar Energy",
            "keywords": ["solar", "PV module", "photovoltaic"],
            "revision_year": 2024,
            "status": "Active (DEMO / SAMPLE DATA)",
            "source_url": None,
            "description": "Solar PV module testing standard.",
            "amendments": [],
            "related_standards": []
        },
        {
            "id": "IS-SEED-002",
            "is_number": "IS SEED 2 : 2024",
            "title": "Submersible Water Pump Sets",
            "scope": "Performance requirements for motor driven water pumps.",
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

    summary = seed_embeddings(standards=sample_standards, engine=engine, session_factory=session_factory)

    assert summary["standards_processed"] == 2
    assert summary["valid_standards"] == 2
    assert summary["embeddings_generated"] == 2
    assert summary["inserted"] == 2
    assert summary["updated"] == 0
    assert summary["skipped"] == 0
    assert summary["failed"] == 0
    assert summary["total_in_db"] == 2

    # Read back records from DB
    session = session_factory()
    rows = session.query(StandardEmbeddingModel).all()
    assert len(rows) == 2

    for row in rows:
        assert row.standard_id in ("IS-SEED-001", "IS-SEED-002")
        assert row.embedding_model == DEFAULT_EMBEDDING_MODEL
        assert row.embedding_dimension == DEFAULT_EMBEDDING_DIMENSION
        assert row.content != ""

    session.close()


def test_empty_and_malformed_standards_handled_safely(sqlite_db):
    """6: Verifies empty, missing id, or non-dict items are handled safely without corrupting DB."""
    engine, session_factory = sqlite_db

    malformed_corpus = [
        "not a dict object",
        {"is_number": "IS NO ID", "title": "Missing ID"},  # missing id
        {"id": "IS-EMPTY-TEXT", "is_number": "", "title": "", "scope": "", "sector": "", "product_category": "", "keywords": []},  # empty content
        {
            "id": "IS-VALID-99",
            "is_number": "IS VALID 99",
            "title": "Valid Title",
            "scope": "Valid scope text for testing",
            "sector": "Testing",
            "product_category": "Testing"
        }
    ]

    summary = seed_embeddings(standards=malformed_corpus, engine=engine, session_factory=session_factory)

    assert summary["standards_processed"] == 4
    assert summary["valid_standards"] == 1
    assert summary["inserted"] == 1
    assert summary["skipped"] == 2  # missing id & empty text
    assert summary["failed"] == 1   # non-dict item
    assert summary["total_in_db"] == 1


def test_seed_embeddings_idempotency_running_twice(sqlite_db):
    """7, 8 & 9: Verifies idempotent execution, duplicate prevention, and update handling on second run."""
    engine, session_factory = sqlite_db

    sample_standards = [
        {
            "id": "IS-IDEM-001",
            "is_number": "IS IDEM 1",
            "title": "Idempotency Test Title",
            "scope": "Scope for idempotency testing",
            "sector": "Testing",
            "product_category": "Testing"
        }
    ]

    # First run: inserts record
    sum1 = seed_embeddings(standards=sample_standards, engine=engine, session_factory=session_factory)
    assert sum1["inserted"] == 1
    assert sum1["updated"] == 0
    assert sum1["total_in_db"] == 1

    # Second run: updates existing record without duplicating
    sum2 = seed_embeddings(standards=sample_standards, engine=engine, session_factory=session_factory)
    assert sum2["inserted"] == 0
    assert sum2["updated"] == 1
    assert sum2["total_in_db"] == 1


def test_faiss_remains_configured_default():
    """11: Verifies that VECTOR_BACKEND configuration remains 'faiss' default baseline."""
    assert VECTOR_BACKEND == "faiss"


def test_cli_fails_explicitly_when_database_unreachable(monkeypatch):
    """10: Verifies CLI entry point exits with code 1 when PostgreSQL database is unreachable."""
    bad_url = "postgresql+psycopg://postgres:invalid@localhost:59999/nonexistent_db"
    monkeypatch.setenv("DATABASE_URL", bad_url)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "true",
    reason="Live PostgreSQL pgvector embedding population test skipped because RUN_POSTGRES_TESTS != 'true'"
)
def test_live_postgresql_pgvector_embedding_seeding():
    """12: Optional live PostgreSQL + pgvector embedding population test under RUN_POSTGRES_TESTS='true'."""
    postgres_url = os.getenv("POSTGRES_TEST_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sih26108_standards")
    engine = create_engine(postgres_url)

    if not check_database_connection(engine):
        pytest.skip("PostgreSQL database server is unreachable at POSTGRES_TEST_URL")

    cap = check_pgvector_extension(engine=engine)
    if not cap.get("pgvector_available", False):
        pytest.skip("PostgreSQL server is reachable, but 'vector' extension is not installed.")

    # Seed live Postgres database with corpus embeddings
    summary = seed_embeddings(engine=engine)
    assert summary["valid_standards"] > 0
    assert summary["total_in_db"] >= 14
