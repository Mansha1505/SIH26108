from backend.database.connection import (
    Base,
    get_db_engine,
    get_session_factory,
    get_db_session,
    check_database_connection
)
from backend.database.models import StandardModel, StandardEmbeddingModel
from backend.database.vector import (
    Vector,
    is_pgvector_package_available,
    get_active_vector_backend,
    check_pgvector_extension
)

__all__ = [
    "Base",
    "StandardModel",
    "StandardEmbeddingModel",
    "get_db_engine",
    "get_session_factory",
    "get_db_session",
    "check_database_connection",
    "load_standards_from_json",
    "seed_standards",
    "clear_standards",
    "build_embedding_content",
    "seed_embeddings",
    "Vector",
    "is_pgvector_package_available",
    "get_active_vector_backend",
    "check_pgvector_extension",
    "load_standards_from_postgres",
    "compare_records",
    "check_embedding_staleness",
    "compare_corpora",
    "synchronize_corpora"
]

def __getattr__(name: str):
    if name in ("load_standards_from_json", "seed_standards", "clear_standards"):
        import backend.database.seed as seed_mod
        return getattr(seed_mod, name)
    if name in ("build_embedding_content", "seed_embeddings"):
        import backend.database.seed_embeddings as seed_emb_mod
        return getattr(seed_emb_mod, name)
    if name in ("load_standards_from_postgres", "compare_records", "check_embedding_staleness", "compare_corpora", "synchronize_corpora"):
        import backend.database.migrate as migrate_mod
        return getattr(migrate_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
