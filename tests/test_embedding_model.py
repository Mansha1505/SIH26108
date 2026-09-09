"""
Unit and Integration Tests for StandardEmbeddingModel (Phase 10B - Chunk 2).

Tests SQLAlchemy StandardEmbeddingModel table creation, pgvector Vector type configuration,
dimension representation, foreign key cascade relationships, duplicate protection unique constraints,
multi-model co-existence, non-blocking imports, and optional live PostgreSQL vector persistence.
"""

import os
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.database.connection import Base, check_database_connection
from backend.database.models import StandardModel, StandardEmbeddingModel
from backend.database.vector import Vector, check_pgvector_extension
from backend.config import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIMENSION


@pytest.fixture
def sqlite_db():
    """Provides an isolated SQLite in-memory engine and session factory with foreign keys enabled."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Enable SQLite foreign key constraints
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield engine, session_factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_embedding_model_import_does_not_require_postgresql():
    """H: Verifies that importing StandardEmbeddingModel does not require a running PostgreSQL server."""
    assert StandardEmbeddingModel is not None
    assert StandardEmbeddingModel.__tablename__ == "standard_embeddings"


def test_embedding_model_table_creation_under_sqlite(sqlite_db):
    """A: Verifies that StandardEmbeddingModel table can be created under SQLite schema definition."""
    engine, session_factory = sqlite_db
    session = session_factory()

    # Create a parent standard
    std = StandardModel(
        id="IS-TEST-001",
        is_number="IS TEST 1 : 2024",
        title="Test Standard Title",
        scope="Test Scope",
        sector="Testing",
        product_category="Testing Category",
        keywords=["test"],
        revision_year=2024,
        status="Active (DEMO / SAMPLE DATA)",
        source_url=None,
        description="Description",
        amendments=[],
        related_standards=[]
    )
    session.add(std)
    session.commit()

    # Query standards count
    assert session.query(StandardModel).count() == 1
    session.close()


def test_vector_column_uses_pgvector_type():
    """B & C: Verifies that embedding column genuinely uses pgvector Vector type with custom dimensions."""
    col_type = StandardEmbeddingModel.embedding.property.columns[0].type
    assert isinstance(col_type, Vector)
    assert col_type.dim == DEFAULT_EMBEDDING_DIMENSION

    # Test explicit dimension representation
    vec_384 = Vector(384)
    vec_1024 = Vector(1024)
    assert vec_384.dim == 384
    assert vec_1024.dim == 1024


def test_embedding_model_metadata_representation(sqlite_db):
    """D: Verifies that a representative embedding record preserves all metadata fields."""
    engine, session_factory = sqlite_db
    session = session_factory()

    std = StandardModel(
        id="IS-TEST-002",
        is_number="IS TEST 2",
        title="Title 2",
        scope="Scope 2",
        sector="Sector 2",
        product_category="Category 2",
        keywords=[],
        revision_year=2024,
        status="Active",
        source_url=None,
        description=None,
        amendments=[],
        related_standards=[]
    )
    session.add(std)
    session.commit()

    emb_record = StandardEmbeddingModel(
        standard_id="IS-TEST-002",
        content="Technical scope content chunk for testing embedding storage",
        embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
        embedding_dimension=384
    )
    session.add(emb_record)
    session.commit()

    retrieved = session.query(StandardEmbeddingModel).filter_by(standard_id="IS-TEST-002").first()
    assert retrieved is not None
    assert retrieved.standard_id == "IS-TEST-002"
    assert retrieved.content == "Technical scope content chunk for testing embedding storage"
    assert retrieved.embedding_model == "paraphrase-multilingual-MiniLM-L12-v2"
    assert retrieved.embedding_dimension == 384
    assert retrieved.created_at is not None

    record_dict = retrieved.to_dict()
    assert record_dict["standard_id"] == "IS-TEST-002"
    assert record_dict["embedding_model"] == "paraphrase-multilingual-MiniLM-L12-v2"
    assert record_dict["embedding_dimension"] == 384

    session.close()


def test_foreign_key_relationship_and_cascade(sqlite_db):
    """E: Verifies relationship linking and cascade delete from StandardModel to StandardEmbeddingModel."""
    engine, session_factory = sqlite_db
    session = session_factory()

    std = StandardModel(
        id="IS-CASCADE-001",
        is_number="IS CASCADE 1",
        title="Cascade Title",
        scope="Cascade Scope",
        sector="Testing",
        product_category="Testing",
        keywords=[],
        revision_year=2024,
        status="Active",
        source_url=None,
        description=None,
        amendments=[],
        related_standards=[]
    )
    session.add(std)
    session.commit()

    emb = StandardEmbeddingModel(
        standard_id="IS-CASCADE-001",
        content="Cascade test content",
        embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
        embedding_dimension=384
    )
    session.add(emb)
    session.commit()

    # Test relationship access
    std_loaded = session.query(StandardModel).filter_by(id="IS-CASCADE-001").first()
    assert len(std_loaded.embeddings) == 1
    assert std_loaded.embeddings[0].content == "Cascade test content"

    # Test cascade deletion
    session.delete(std_loaded)
    session.commit()

    assert session.query(StandardEmbeddingModel).filter_by(standard_id="IS-CASCADE-001").count() == 0
    session.close()


def test_duplicate_protection_unique_constraint(sqlite_db):
    """F: Verifies duplicate protection unique constraint (standard_id, content, embedding_model)."""
    engine, session_factory = sqlite_db
    session = session_factory()

    std = StandardModel(
        id="IS-DUPLICATE-001",
        is_number="IS DUP 1",
        title="Dup Title",
        scope="Dup Scope",
        sector="Testing",
        product_category="Testing",
        keywords=[],
        revision_year=2024,
        status="Active",
        source_url=None,
        description=None,
        amendments=[],
        related_standards=[]
    )
    session.add(std)
    session.commit()

    emb1 = StandardEmbeddingModel(
        standard_id="IS-DUPLICATE-001",
        content="Exact duplicate content chunk",
        embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
        embedding_dimension=384
    )
    session.add(emb1)
    session.commit()

    # Attempt to insert identical duplicate record
    emb2 = StandardEmbeddingModel(
        standard_id="IS-DUPLICATE-001",
        content="Exact duplicate content chunk",
        embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
        embedding_dimension=384
    )
    session.add(emb2)
    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()
    session.close()


def test_multiple_embedding_models_coexistence(sqlite_db):
    """G: Verifies that multiple embedding models (e.g. MiniLM 384 and BGE-M3 1024) can coexist for the same standard."""
    engine, session_factory = sqlite_db
    session = session_factory()

    std = StandardModel(
        id="IS-MULTI-MODEL-001",
        is_number="IS MULTI 1",
        title="Multi Model Title",
        scope="Multi Model Scope",
        sector="Testing",
        product_category="Testing",
        keywords=[],
        revision_year=2024,
        status="Active",
        source_url=None,
        description=None,
        amendments=[],
        related_standards=[]
    )
    session.add(std)
    session.commit()

    # Record 1: MiniLM 384
    emb_minilm = StandardEmbeddingModel(
        standard_id="IS-MULTI-MODEL-001",
        content="Multi model scope text",
        embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
        embedding_dimension=384
    )
    # Record 2: BGE-M3 1024
    emb_bgem3 = StandardEmbeddingModel(
        standard_id="IS-MULTI-MODEL-001",
        content="Multi model scope text",
        embedding_model="BAAI/bge-m3",
        embedding_dimension=1024
    )

    session.add_all([emb_minilm, emb_bgem3])
    session.commit()

    records = session.query(StandardEmbeddingModel).filter_by(standard_id="IS-MULTI-MODEL-001").all()
    assert len(records) == 2

    models_in_db = {r.embedding_model: r.embedding_dimension for r in records}
    assert models_in_db["paraphrase-multilingual-MiniLM-L12-v2"] == 384
    assert models_in_db["BAAI/bge-m3"] == 1024

    session.close()


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "true",
    reason="Live PostgreSQL pgvector persistence test skipped because RUN_POSTGRES_TESTS != 'true'"
)
def test_live_postgresql_vector_persistence():
    """13: Optional live PostgreSQL integration test inserting and reading back a real pgvector embedding."""
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

    test_std_id = "IS-PGVEC-LIVE-001"
    try:
        # Clean up any residual test data
        session.query(StandardEmbeddingModel).filter_by(standard_id=test_std_id).delete()
        session.query(StandardModel).filter_by(id=test_std_id).delete()
        session.commit()

        # Insert parent standard
        std = StandardModel(
            id=test_std_id,
            is_number="IS PGVEC LIVE 1",
            title="Live PGVector Test Title",
            scope="Live PGVector Scope",
            sector="Testing",
            product_category="Testing",
            keywords=[],
            revision_year=2024,
            status="Active",
            source_url=None,
            description=None,
            amendments=[],
            related_standards=[]
        )
        session.add(std)
        session.commit()

        # Generate sample 384-dim dummy vector
        dummy_vec = [float(i) / 384.0 for i in range(384)]

        emb_rec = StandardEmbeddingModel(
            standard_id=test_std_id,
            content="Live PGVector content chunk",
            embedding=dummy_vec,
            embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
            embedding_dimension=384
        )
        session.add(emb_rec)
        session.commit()

        retrieved = session.query(StandardEmbeddingModel).filter_by(standard_id=test_std_id).first()
        assert retrieved is not None
        assert retrieved.embedding is not None
        assert len(retrieved.embedding) == 384
        assert abs(retrieved.embedding[0] - 0.0) < 1e-5

    finally:
        # Clean up test data
        session.query(StandardEmbeddingModel).filter_by(standard_id=test_std_id).delete()
        session.query(StandardModel).filter_by(id=test_std_id).delete()
        session.commit()
        session.close()
