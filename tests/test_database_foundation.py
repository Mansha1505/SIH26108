import pytest
import os
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.orm import Session

from backend.config import (
    DATABASE_URL,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_ECHO,
    REPOSITORY_TYPE
)
from backend.database.connection import (
    Base,
    get_db_engine,
    get_session_factory,
    get_db_session,
    check_database_connection
)
from backend.retrieval.loader import (
    get_default_repository,
    JsonStandardsRepository,
    PostgresStandardsRepository
)
from backend.services.recommendation_service import service_instance
from backend.models.schemas import RecommendationRequest


def test_database_config_defaults():
    """1. Test that database configuration settings are loaded properly from config."""
    assert DATABASE_URL is not None
    assert "postgresql" in DATABASE_URL
    assert isinstance(DB_POOL_SIZE, int)
    assert isinstance(DB_MAX_OVERFLOW, int)
    assert isinstance(DB_POOL_TIMEOUT, float)
    assert isinstance(DB_ECHO, bool)
    assert REPOSITORY_TYPE == "json"


def test_database_engine_and_session_factory_creation():
    """2. Test SQLAlchemy engine and session factory creation with custom SQLite URL (offline mode)."""
    # Use SQLite in-memory for testing SQLAlchemy foundation without requiring live Postgres server
    test_url = "sqlite:///:memory:"
    engine = get_db_engine(database_url=test_url, force_new=True)
    assert engine is not None
    assert engine.dialect.name == "sqlite"

    session_factory = get_session_factory(engine=engine, force_new=True)
    session = session_factory()
    assert isinstance(session, Session)
    session.close()


def test_declarative_base_and_table_creation():
    """3. Test Declarative Base model inheritance and table creation using SQLite in-memory."""
    class DummyTestModel(Base):
        __tablename__ = "dummy_test_table"
        id = Column(Integer, primary_key=True)
        name = Column(String(50), nullable=False)

    test_url = "sqlite:///:memory:"
    engine = get_db_engine(database_url=test_url, force_new=True)
    Base.metadata.create_all(bind=engine)

    session_factory = get_session_factory(engine=engine, force_new=True)
    with session_factory() as session:
        dummy_item = DummyTestModel(id=1, name="Test Standard Record")
        session.add(dummy_item)
        session.commit()

        retrieved = session.query(DummyTestModel).filter_by(id=1).first()
        assert retrieved is not None
        assert retrieved.name == "Test Standard Record"


def test_check_database_connection_graceful_handling():
    """4. Test database connection check returns True for active DB and False for unreachable DB without crashing."""
    # Active SQLite in-memory connection
    test_url = "sqlite:///:memory:"
    valid_engine = get_db_engine(database_url=test_url, force_new=True)
    assert check_database_connection(engine=valid_engine) is True

    # Unreachable database connection test (SQLite non-existent path)
    invalid_url = "sqlite:////invalid_directory_path_12345/non_existent.db"
    invalid_engine = get_db_engine(database_url=invalid_url, force_new=True)
    assert check_database_connection(engine=invalid_engine) is False


def test_json_repository_baseline_remains_unchanged():
    """5. Test that JsonStandardsRepository remains active baseline and recommendation system functions as expected."""
    repo = get_default_repository()
    assert isinstance(repo, JsonStandardsRepository)

    standards = repo.get_all_standards()
    assert len(standards) == 14
    assert any(s["is_number"].startswith("IS 1180") for s in standards)

    # Verify recommendation service works normally
    if not service_instance._is_initialized:
        service_instance.initialize()

    rec_res = service_instance.recommend(RecommendationRequest(query="100 kVA distribution transformer", top_k=2))
    assert len(rec_res.recommendations) == 2
    assert "IS 1180" in rec_res.recommendations[0].is_number


def test_standard_model_orm_persistence_and_conversion():
    """6. Test StandardModel persistence in SQLite in-memory and ORM <-> Pydantic schema conversion."""
    from backend.database.models import StandardModel
    from backend.models.schemas import IndianStandardRecord

    sample_record = IndianStandardRecord(
        id="IS-1180-P1",
        is_number="IS 1180 (Part 1) : 2014",
        title="Outdoor Type Oil Imversed Distribution Transformers",
        scope="Specification for distribution transformers up to 2500 kVA, 33 kV.",
        sector="Electrical Engineering",
        product_category="Transformers",
        keywords=["transformer", "distribution transformer", "oil immersed", "11kv"],
        revision_year=2014,
        status="Active (DEMO / SAMPLE DATA)",
        source_url="https://bis.gov.in/demo/1180",
        description="Standard specification for mineral oil filled distribution transformers.",
        amendments=[{"amendment_number": 1, "year": 2016, "title": "Amendment 1"}],
        related_standards=["IS 2026 (Part 1)", "IS 335"]
    )

    # Convert Pydantic -> ORM Model
    orm_model = StandardModel.from_pydantic(sample_record)
    assert orm_model.id == "IS-1180-P1"
    assert orm_model.is_number == "IS 1180 (Part 1) : 2014"

    # Test SQLite in-memory persistence of complex JSON fields (keywords, amendments, related_standards)
    test_url = "sqlite:///:memory:"
    engine = get_db_engine(database_url=test_url, force_new=True)
    Base.metadata.create_all(bind=engine)
    session_factory = get_session_factory(engine=engine, force_new=True)

    with session_factory() as session:
        session.add(orm_model)
        session.commit()

        # Query back from DB
        fetched = session.query(StandardModel).filter_by(id="IS-1180-P1").first()
        assert fetched is not None
        assert fetched.is_number == "IS 1180 (Part 1) : 2014"

        # Convert ORM Model -> Pydantic Model
        pydantic_res = fetched.to_pydantic()
        assert isinstance(pydantic_res, IndianStandardRecord)
        assert pydantic_res.id == "IS-1180-P1"
        assert pydantic_res.keywords == ["transformer", "distribution transformer", "oil immersed", "11kv"]
        assert len(pydantic_res.amendments) == 1
        assert pydantic_res.amendments[0]["amendment_number"] == 1
        assert pydantic_res.related_standards == ["IS 2026 (Part 1)", "IS 335"]


def test_postgres_standards_repository_queries():
    """7. Test PostgresStandardsRepository methods (get_all_standards, get_standard_by_id, get_standard_by_is_number)."""
    from backend.database.models import StandardModel
    from backend.models.schemas import IndianStandardRecord

    test_url = "sqlite:///:memory:"
    engine = get_db_engine(database_url=test_url, force_new=True)
    Base.metadata.create_all(bind=engine)
    session_factory = get_session_factory(engine=engine, force_new=True)

    rec1 = IndianStandardRecord(
        id="IS-7098-P2",
        is_number="IS 7098 (Part 2) : 2011",
        title="XLPE Insulated Cables",
        scope="Working voltages from 3.3 kV up to 33 kV",
        sector="Electrical Cables",
        product_category="Electrical Cables",
        keywords=["xlpe", "cable", "11 kv"],
        revision_year=2011,
        status="Active (DEMO / SAMPLE DATA)",
        amendments=[],
        related_standards=["IS 7098 (Part 1)"]
    )
    rec2 = IndianStandardRecord(
        id="IS-4984-2016",
        is_number="IS 4984 : 2016",
        title="High Density Polyethylene Pipes for Water Supply",
        scope="HDPE pipes for potable water supply",
        sector="Civil & Water",
        product_category="Pipes & Fittings",
        keywords=["hdpe", "pipe", "water supply"],
        revision_year=2016,
        status="Active (DEMO / SAMPLE DATA)",
        amendments=[],
        related_standards=[]
    )

    with session_factory() as session:
        session.add(StandardModel.from_pydantic(rec1))
        session.add(StandardModel.from_pydantic(rec2))
        session.commit()

    repo = PostgresStandardsRepository(session_factory=session_factory)

    # 1. get_all_standards
    all_stds = repo.get_all_standards()
    assert len(all_stds) == 2
    assert any(s["id"] == "IS-7098-P2" for s in all_stds)
    assert any(s["id"] == "IS-4984-2016" for s in all_stds)

    # 2. get_standard_by_id
    by_id = repo.get_standard_by_id("IS-7098-P2")
    assert by_id is not None
    assert by_id["is_number"] == "IS 7098 (Part 2) : 2011"
    assert repo.get_standard_by_id("IS-NON-EXISTENT") is None

    # 3. get_standard_by_is_number
    by_is = repo.get_standard_by_is_number("is 4984 : 2016")
    assert by_is is not None
    assert by_is["id"] == "IS-4984-2016"
    assert repo.get_standard_by_is_number("IS 99999") is None


def test_default_repository_factory_selection(monkeypatch):
    """8. Test that get_default_repository respects REPOSITORY_TYPE env var while defaulting to JSON."""
    # Default is JSON
    monkeypatch.delenv("REPOSITORY_TYPE", raising=False)
    default_repo = get_default_repository()
    assert isinstance(default_repo, JsonStandardsRepository)

    # Set REPOSITORY_TYPE=postgres
    monkeypatch.setenv("REPOSITORY_TYPE", "postgres")
    postgres_repo = get_default_repository()
    assert isinstance(postgres_repo, PostgresStandardsRepository)

