"""
Unit and Integration Tests for Standards Database Seed Utility (Phase 10A - Chunk 3).

Tests loading, Pydantic validation, idempotent seeding, round-trip serialization,
rollback handling, malformed input rejection, and repository baseline integrity.
"""

import os
import json
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.connection import Base, check_database_connection
from backend.database.models import StandardModel
from backend.database.seed import (
    load_standards_from_json,
    seed_standards,
    clear_standards
)
from backend.retrieval.loader import (
    PostgresStandardsRepository,
    JsonStandardsRepository,
    get_default_repository
)
from backend.models.schemas import IndianStandardRecord


@pytest.fixture
def memory_db():
    """Provides an isolated SQLite in-memory database engine and session factory."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield engine, session_factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_json_corpus_loads_and_validates():
    """1 & 2: Verifies that the JSON standards corpus loads and all records validate against IndianStandardRecord schema."""
    records = load_standards_from_json()
    assert len(records) > 0
    for record in records:
        assert isinstance(record, IndianStandardRecord)
        assert record.id is not None
        assert record.is_number is not None
        assert record.title is not None
        assert record.sector is not None


def test_seed_standards_populates_expected_count(memory_db):
    """3 & 8: Verifies seed populates DB with dynamic corpus count matching load_standards_from_json()."""
    engine, session_factory = memory_db
    records = load_standards_from_json()
    expected_count = len(records)

    stats = seed_standards(engine=engine, session_factory=session_factory)
    assert stats["total_processed"] == expected_count
    assert stats["inserted"] == expected_count
    assert stats["updated"] == 0
    assert stats["total_in_db"] == expected_count

    # Verify via repository read
    repo = PostgresStandardsRepository(session_factory=session_factory, engine=engine)
    retrieved = repo.get_all_standards()
    assert len(retrieved) == expected_count


def test_seeded_records_read_back_and_structure_preserved(memory_db):
    """4 & 5: Verifies seeded records read back cleanly with intact keywords, amendments, and related_standards."""
    engine, session_factory = memory_db
    seed_standards(engine=engine, session_factory=session_factory)

    repo = PostgresStandardsRepository(session_factory=session_factory, engine=engine)
    
    # Check IS-10322-P5-S3 which has keywords, amendments, and related_standards
    record_dict = repo.get_standard_by_id("IS-10322-P5-S3")
    assert record_dict is not None
    assert record_dict["id"] == "IS-10322-P5-S3"
    assert record_dict["is_number"] == "IS 10322 (Part 5/Sec 3) : 2012"
    assert isinstance(record_dict["keywords"], list)
    assert "LED" in record_dict["keywords"]
    assert isinstance(record_dict["amendments"], list)
    assert len(record_dict["amendments"]) > 0
    assert record_dict["amendments"][0]["amendment_number"] == 1
    assert isinstance(record_dict["related_standards"], list)
    assert len(record_dict["related_standards"]) > 0


def test_seed_idempotency_running_twice(memory_db):
    """6: Verifies running seed twice does not create duplicate rows or increase count."""
    engine, session_factory = memory_db
    records = load_standards_from_json()
    expected_count = len(records)

    stats1 = seed_standards(engine=engine, session_factory=session_factory)
    assert stats1["inserted"] == expected_count

    stats2 = seed_standards(engine=engine, session_factory=session_factory)
    assert stats2["inserted"] == 0
    assert stats2["updated"] == expected_count
    assert stats2["total_in_db"] == expected_count


def test_seed_updates_existing_record_on_data_change(tmp_path, memory_db):
    """7: Verifies existing record is updated in-place rather than duplicated when source JSON changes."""
    engine, session_factory = memory_db

    # Create temporary JSON corpus with 1 record
    sample_corpus = [
        {
            "id": "IS-TEST-001",
            "is_number": "IS TEST 1 : 2024",
            "title": "Initial Title",
            "scope": "Test scope",
            "sector": "Testing",
            "product_category": "Test Category",
            "keywords": ["test"],
            "revision_year": 2024,
            "status": "Active (DEMO / SAMPLE DATA)",
            "source_url": None,
            "description": "Initial description",
            "amendments": [],
            "related_standards": []
        }
    ]
    test_json_file = tmp_path / "test_standards.json"
    test_json_file.write_text(json.dumps(sample_corpus), encoding="utf-8")

    # Initial seed
    stats1 = seed_standards(json_path=str(test_json_file), engine=engine, session_factory=session_factory)
    assert stats1["inserted"] == 1
    assert stats1["updated"] == 0

    # Modify title in JSON
    sample_corpus[0]["title"] = "Updated Title after modification"
    test_json_file.write_text(json.dumps(sample_corpus), encoding="utf-8")

    # Re-seed
    stats2 = seed_standards(json_path=str(test_json_file), engine=engine, session_factory=session_factory)
    assert stats2["inserted"] == 0
    assert stats2["updated"] == 1
    assert stats2["total_in_db"] == 1

    # Verify update
    repo = PostgresStandardsRepository(session_factory=session_factory, engine=engine)
    updated_rec = repo.get_standard_by_id("IS-TEST-001")
    assert updated_rec["title"] == "Updated Title after modification"


def test_seed_transaction_rollback_on_failure(tmp_path, memory_db):
    """8: Verifies session transaction rollback occurs when invalid/malformed data is encountered."""
    engine, session_factory = memory_db

    # Create temp JSON file containing 1 valid record and 1 malformed record
    malformed_corpus = [
        {
            "id": "IS-VALID-001",
            "is_number": "IS VALID 1",
            "title": "Valid Standard",
            "scope": "Valid scope",
            "sector": "Electrotechnical",
            "product_category": "Testing",
            "keywords": [],
            "revision_year": 2024,
            "status": "Active (DEMO / SAMPLE DATA)",
            "source_url": None,
            "description": "Desc",
            "amendments": [],
            "related_standards": []
        },
        {
            "id": "IS-INVALID-002",
            # Missing required 'title', 'scope', 'sector', etc.
            "is_number": "IS INVALID 2"
        }
    ]
    test_json_file = tmp_path / "malformed_standards.json"
    test_json_file.write_text(json.dumps(malformed_corpus), encoding="utf-8")

    with pytest.raises(Exception):
        seed_standards(json_path=str(test_json_file), engine=engine, session_factory=session_factory)

    # Verify DB remains completely empty due to atomic validation & rollback
    session = session_factory()
    count = session.query(StandardModel).count()
    session.close()
    assert count == 0


def test_malformed_json_input_rejected_safely(tmp_path):
    """9: Verifies non-existent file or malformed JSON structure raises appropriate exception."""
    non_existent = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        load_standards_from_json(str(non_existent))

    invalid_json_file = tmp_path / "invalid.json"
    invalid_json_file.write_text("{ not valid json }", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_standards_from_json(str(invalid_json_file))


def test_json_repository_baseline_remains_unchanged():
    """10: Verifies default REPOSITORY_TYPE='json' and JsonStandardsRepository baseline are untouched."""
    default_repo = get_default_repository()
    assert isinstance(default_repo, JsonStandardsRepository)

    json_repo = JsonStandardsRepository()
    all_json_stds = json_repo.get_all_standards()
    assert len(all_json_stds) == 14  # Current corpus length


def test_demo_corpus_count_matches_db_count_after_seed(memory_db):
    """11: Proves demo corpus count dynamically matches DB count after seeding."""
    engine, session_factory = memory_db
    json_records = load_standards_from_json()

    seed_standards(engine=engine, session_factory=session_factory)

    repo = PostgresStandardsRepository(session_factory=session_factory, engine=engine)
    db_records = repo.get_all_standards()

    assert len(json_records) == len(db_records)


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "true",
    reason="Live PostgreSQL integration test skipped because RUN_POSTGRES_TESTS != 'true'"
)
def test_live_postgresql_integration():
    """12: Optional integration test running only when RUN_POSTGRES_TESTS='true' environment variable is explicitly set."""
    postgres_url = os.getenv("POSTGRES_TEST_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sih26108_test")
    engine = create_engine(postgres_url)
    if not check_database_connection(engine):
        pytest.skip("PostgreSQL database is unreachable at POSTGRES_TEST_URL")

    stats = seed_standards(engine=engine)
    assert stats["total_in_db"] > 0
