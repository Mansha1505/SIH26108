"""
Unit and Integration Tests for Database Migration & Synchronization Engine (Phase 10C).

Tests JSON corpus loading, PostgreSQL corpus comparison, missing/extra/changed record detection,
embedding staleness detection, idempotent synchronization, safe deletion defaults, and backend baseline defaults.
"""

import os
import json
import pytest
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.database.connection import Base
from backend.database.models import StandardModel, StandardEmbeddingModel
from backend.database.seed import seed_standards, load_standards_from_json
from backend.database.seed_embeddings import seed_embeddings, build_embedding_content
from backend.database.migrate import (
    load_standards_from_postgres,
    compare_records,
    check_embedding_staleness,
    compare_corpora,
    synchronize_corpora
)
from backend.models.schemas import IndianStandardRecord
from backend.config import REPOSITORY_TYPE, VECTOR_BACKEND, DEFAULT_EMBEDDING_MODEL


class DummyEmbeddingEngine:
    """Fast dummy embedding engine for unit testing migration without loading torch models."""
    def __init__(self, standards=None, model_name=DEFAULT_EMBEDDING_MODEL):
        self.active_model_name = model_name
        self.vector_dimension = 384
        count = len(standards) if standards is not None else 0
        self.doc_embeddings = np.random.rand(count, 384).astype(np.float32)


@pytest.fixture
def memory_db_engine():
    """Provides a fresh SQLite in-memory database engine for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def memory_session_factory(memory_db_engine):
    """Provides a session factory bound to the in-memory database engine."""
    return sessionmaker(bind=memory_db_engine)


@pytest.fixture
def sample_json_file(tmp_path):
    """Creates a temporary JSON file with sample standards records."""
    sample_records = [
        {
            "id": "IS-101",
            "is_number": "IS 101:2020",
            "title": "Paint and Varnish Standard",
            "scope": "Specification for decorative paint quality.",
            "sector": "Chemical",
            "product_category": "Paints",
            "keywords": ["paint", "varnish", "coating"],
            "revision_year": 2020,
            "status": "Active (DEMO / SAMPLE DATA)",
            "source_url": "https://bis.gov.in/is101",
            "description": "Standard overview for paint products.",
            "amendments": [],
            "related_standards": ["IS-102"]
        },
        {
            "id": "IS-102",
            "is_number": "IS 102:2021",
            "title": "Steel Bar Standard",
            "scope": "Specification for reinforced steel bars.",
            "sector": "Metallurgy",
            "product_category": "Steel",
            "keywords": ["steel", "rebar"],
            "revision_year": 2021,
            "status": "Active (DEMO / SAMPLE DATA)",
            "source_url": "https://bis.gov.in/is102",
            "description": "Standard overview for steel rebar.",
            "amendments": [],
            "related_standards": ["IS-101"]
        }
    ]
    file_path = tmp_path / "test_standards.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_records, f, indent=2)
    return str(file_path)


# 1. JSON corpus loading test
def test_json_corpus_loading(sample_json_file):
    records = load_standards_from_json(sample_json_file)
    assert len(records) == 2
    assert records[0].id == "IS-101"
    assert records[1].id == "IS-102"
    assert isinstance(records[0], IndianStandardRecord)


# 2. PostgreSQL corpus loading and comparison
def test_postgres_corpus_loading_and_comparison(sample_json_file, memory_db_engine, memory_session_factory):
    # Seed DB with JSON data
    seed_standards(json_path=sample_json_file, engine=memory_db_engine, session_factory=memory_session_factory)
    
    pg_records = load_standards_from_postgres(engine=memory_db_engine, session_factory=memory_session_factory)
    assert len(pg_records) == 2
    assert pg_records[0]["id"] in ["IS-101", "IS-102"]


# 3. Identical corpus detection
def test_identical_corpus_detection(sample_json_file, memory_db_engine, memory_session_factory):
    seed_standards(json_path=sample_json_file, engine=memory_db_engine, session_factory=memory_session_factory)
    dummy_engine = DummyEmbeddingEngine(standards=load_standards_from_json(sample_json_file))
    seed_embeddings(
        standards=[r.model_dump() for r in load_standards_from_json(sample_json_file)],
        engine=memory_db_engine,
        session_factory=memory_session_factory,
        embedding_engine=dummy_engine
    )

    report = compare_corpora(
        json_path=sample_json_file,
        engine=memory_db_engine,
        session_factory=memory_session_factory
    )

    assert report["json_count"] == 2
    assert report["postgres_count"] == 2
    assert report["identical_count"] == 2
    assert len(report["missing_in_postgres"]) == 0
    assert len(report["extra_in_postgres"]) == 0
    assert len(report["changed_records"]) == 0
    assert len(report["stale_embeddings"]) == 0
    assert report["synchronization_status"] == "IN_SYNC"


# 4. Missing-record detection
def test_missing_record_detection(sample_json_file, memory_db_engine, memory_session_factory):
    # DB has zero records initially
    report = compare_corpora(
        json_path=sample_json_file,
        engine=memory_db_engine,
        session_factory=memory_session_factory
    )

    assert report["json_count"] == 2
    assert report["postgres_count"] == 0
    assert len(report["missing_in_postgres"]) == 2
    assert "IS-101" in report["missing_in_postgres"]
    assert "IS-102" in report["missing_in_postgres"]
    assert report["synchronization_status"] == "EMPTY_POSTGRES"


# 5. Extra-record detection
def test_extra_record_detection(sample_json_file, memory_db_engine, memory_session_factory):
    seed_standards(json_path=sample_json_file, engine=memory_db_engine, session_factory=memory_session_factory)
    
    # Insert extra record directly into DB
    session = memory_session_factory()
    extra_orm = StandardModel(
        id="IS-999-EXTRA",
        is_number="IS 999:2022",
        title="Extra Standard",
        scope="Extra test standard scope.",
        sector="Testing",
        product_category="Test",
        keywords=["extra"],
        revision_year=2022,
        status="Active (DEMO / SAMPLE DATA)",
        source_url=None,
        description=None,
        amendments=[],
        related_standards=[]
    )
    session.add(extra_orm)
    session.commit()
    session.close()

    report = compare_corpora(
        json_path=sample_json_file,
        engine=memory_db_engine,
        session_factory=memory_session_factory
    )

    assert report["postgres_count"] == 3
    assert len(report["extra_in_postgres"]) == 1
    assert report["extra_in_postgres"][0] == "IS-999-EXTRA"
    assert report["synchronization_status"] == "OUT_OF_SYNC"


# 6. Changed-record detection
def test_changed_record_detection(sample_json_file, memory_db_engine, memory_session_factory):
    seed_standards(json_path=sample_json_file, engine=memory_db_engine, session_factory=memory_session_factory)

    # Mutate record title in DB
    session = memory_session_factory()
    std = session.query(StandardModel).filter(StandardModel.id == "IS-101").first()
    std.title = "MUTATED Paint Standard Title"
    session.commit()
    session.close()

    report = compare_corpora(
        json_path=sample_json_file,
        engine=memory_db_engine,
        session_factory=memory_session_factory
    )

    assert len(report["changed_records"]) == 1
    chg = report["changed_records"][0]
    assert chg["id"] == "IS-101"
    assert "title" in chg["diffs"]
    assert chg["diffs"]["title"]["json"] == "Paint and Varnish Standard"
    assert chg["diffs"]["title"]["postgres"] == "MUTATED Paint Standard Title"
    assert report["synchronization_status"] == "OUT_OF_SYNC"


# 7. Deterministic comparison output format
def test_deterministic_comparison_output_format(sample_json_file, memory_db_engine, memory_session_factory):
    report = compare_corpora(
        json_path=sample_json_file,
        engine=memory_db_engine,
        session_factory=memory_session_factory
    )
    expected_keys = {
        "json_count",
        "postgres_count",
        "identical_count",
        "missing_in_postgres",
        "extra_in_postgres",
        "changed_records",
        "stale_embeddings",
        "synchronization_status"
    }
    assert set(report.keys()) == expected_keys
    # Ensure lists are sorted deterministically
    assert isinstance(report["missing_in_postgres"], list)
    assert report["missing_in_postgres"] == sorted(report["missing_in_postgres"])


# 8. Idempotent synchronization
def test_idempotent_synchronization(sample_json_file, memory_db_engine, memory_session_factory):
    dummy_engine = DummyEmbeddingEngine(standards=load_standards_from_json(sample_json_file))
    
    # Run 1
    res1 = synchronize_corpora(
        json_path=sample_json_file,
        engine=memory_db_engine,
        session_factory=memory_session_factory,
        embedding_engine=dummy_engine
    )
    assert res1["status"] == "SUCCESS"
    assert res1["inserted"] == 2

    # Run 2 (Should be idempotent with 0 inserted, 0 updated)
    res2 = synchronize_corpora(
        json_path=sample_json_file,
        engine=memory_db_engine,
        session_factory=memory_session_factory,
        embedding_engine=dummy_engine
    )
    assert res2["status"] == "SUCCESS"
    assert res2["inserted"] == 0
    assert res2["updated"] == 0


# 9. No destructive deletion by default
def test_no_destructive_deletion_by_default(sample_json_file, memory_db_engine, memory_session_factory):
    seed_standards(json_path=sample_json_file, engine=memory_db_engine, session_factory=memory_session_factory)
    
    # Add extra record directly to DB
    session = memory_session_factory()
    extra_orm = StandardModel(
        id="IS-EXTRA-88",
        is_number="IS 88:2020",
        title="Extra Standard 88",
        scope="Extra scope",
        sector="Misc",
        product_category="Misc",
        keywords=[],
        revision_year=2020,
        status="Active (DEMO / SAMPLE DATA)",
        source_url=None,
        description=None,
        amendments=[],
        related_standards=[]
    )
    session.add(extra_orm)
    session.commit()
    session.close()

    dummy_engine = DummyEmbeddingEngine(standards=load_standards_from_json(sample_json_file))

    # Sync with default delete_extra=False
    sync_res = synchronize_corpora(
        json_path=sample_json_file,
        engine=memory_db_engine,
        session_factory=memory_session_factory,
        delete_extra=False,
        embedding_engine=dummy_engine
    )

    assert sync_res["deleted_extra"] == 0
    assert sync_res["final_postgres_count"] == 3  # 2 from JSON + 1 extra preserved

    # Sync with explicit delete_extra=True
    sync_res_del = synchronize_corpora(
        json_path=sample_json_file,
        engine=memory_db_engine,
        session_factory=memory_session_factory,
        delete_extra=True,
        embedding_engine=dummy_engine
    )

    assert sync_res_del["deleted_extra"] == 1
    assert sync_res_del["final_postgres_count"] == 2


# 10. Embedding staleness detection when standard content changes
def test_embedding_staleness_detection(sample_json_file, memory_db_engine, memory_session_factory):
    seed_standards(json_path=sample_json_file, engine=memory_db_engine, session_factory=memory_session_factory)
    records = load_standards_from_json(sample_json_file)
    dummy_engine = DummyEmbeddingEngine(standards=records)
    seed_embeddings(
        standards=[r.model_dump() for r in records],
        engine=memory_db_engine,
        session_factory=memory_session_factory,
        embedding_engine=dummy_engine
    )

    # Initial check: clean
    stale_initial = check_embedding_staleness(engine=memory_db_engine, session_factory=memory_session_factory)
    assert len(stale_initial) == 0

    # Mutate description in DB
    session = memory_session_factory()
    std = session.query(StandardModel).filter(StandardModel.id == "IS-101").first()
    std.description = "NEW MODIFIED DESCRIPTION THAT CHANGES TEXT CONTENT"
    session.commit()
    session.close()

    # Staleness check should flag IS-101
    stale_after = check_embedding_staleness(engine=memory_db_engine, session_factory=memory_session_factory)
    assert len(stale_after) == 1
    assert stale_after[0]["standard_id"] == "IS-101"
    assert stale_after[0]["reason"] == "stale_content"


# 11. Handling empty corpus gracefully
def test_empty_corpus_handling(tmp_path, memory_db_engine, memory_session_factory):
    empty_file = tmp_path / "empty_standards.json"
    with open(empty_file, "w", encoding="utf-8") as f:
        json.dump([], f)

    report = compare_corpora(
        json_path=str(empty_file),
        engine=memory_db_engine,
        session_factory=memory_session_factory
    )
    assert report["json_count"] == 0
    assert report["postgres_count"] == 0
    assert report["synchronization_status"] == "EMPTY_POSTGRES"


# 12. Handling invalid corpus gracefully
def test_invalid_corpus_handling(tmp_path):
    invalid_file = tmp_path / "invalid.json"
    with open(invalid_file, "w", encoding="utf-8") as f:
        f.write("NOT VALID JSON")

    with pytest.raises(Exception):
        load_standards_from_json(str(invalid_file))


# 13. Repository and default configuration preserved
def test_default_configuration_preserved():
    assert REPOSITORY_TYPE == "json"
    assert VECTOR_BACKEND == "faiss"


# 14. Optional Live PostgreSQL Migration Test
@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS", "false").lower() != "true",
    reason="Live PostgreSQL tests require RUN_POSTGRES_TESTS='true' and an active PostgreSQL database."
)
def test_live_postgres_migration():
    from backend.database.connection import get_db_engine, check_database_connection
    engine = get_db_engine(force_new=True)
    assert check_database_connection(engine), "Live PostgreSQL connection failed."

    # Perform comparison on live Postgres DB
    report = compare_corpora(engine=engine)
    assert "synchronization_status" in report
    assert isinstance(report["json_count"], int)
    assert isinstance(report["postgres_count"], int)
