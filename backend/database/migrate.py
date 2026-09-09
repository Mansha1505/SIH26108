"""
Corpus Migration, Comparison, and Synchronization Engine for SIH26108 Standards Intelligence (Phase 10C).

Provides deterministic comparison between the JSON reference corpus and the PostgreSQL standards table.
Supports field-level diffing, embedding staleness detection, idempotent synchronization, and explicit CLI execution.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.database.connection import (
    Base,
    get_db_engine,
    get_session_factory,
    check_database_connection
)
from backend.database.models import StandardModel, StandardEmbeddingModel
from backend.database.seed import load_standards_from_json
from backend.database.seed_embeddings import build_embedding_content, seed_embeddings
from backend.models.schemas import IndianStandardRecord
from backend.config import (
    DEFAULT_EMBEDDING_MODEL,
    DATABASE_URL,
    REPOSITORY_TYPE,
    VECTOR_BACKEND
)
from backend.utils.logger import get_logger

logger = get_logger("DatabaseMigrate")

MEANINGFUL_FIELDS = [
    "id",
    "is_number",
    "title",
    "scope",
    "sector",
    "product_category",
    "keywords",
    "revision_year",
    "status",
    "source_url",
    "description",
    "amendments",
    "related_standards",
]


def load_standards_from_postgres(
    engine: Optional[Any] = None,
    session_factory: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Loads all standard records from the database.
    
    Returns a list of standard dictionaries matching the IndianStandardRecord schema.
    """
    active_engine = engine or get_db_engine()
    factory = session_factory or get_session_factory(engine=active_engine)
    session: Session = factory()
    try:
        models = session.query(StandardModel).order_by(StandardModel.id).all()
        return [m.to_dict() for m in models]
    except Exception as e:
        logger.error(f"Error loading standards from database: {e}")
        raise
    finally:
        session.close()


def normalize_val(val: Any) -> Any:
    """Normalizes field values for deterministic comparisons across JSON and database formats."""
    if val is None:
        return None
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, list):
        return [normalize_val(item) for item in val]
    if isinstance(val, dict):
        return {k: normalize_val(v) for k, v in sorted(val.items())}
    return val


def compare_records(json_rec: Dict[str, Any], pg_rec: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Compares two standard records across all meaningful fields.
    
    Returns:
        (is_identical: bool, diffs: Dict[field_name, {"json": val, "postgres": val}])
    """
    diffs: Dict[str, Any] = {}
    for field in MEANINGFUL_FIELDS:
        val_json = normalize_val(json_rec.get(field))
        val_pg = normalize_val(pg_rec.get(field))

        if val_json != val_pg:
            diffs[field] = {
                "json": val_json,
                "postgres": val_pg
            }

    return (len(diffs) == 0, diffs)


def check_embedding_staleness(
    engine: Optional[Any] = None,
    session_factory: Optional[Any] = None,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
) -> List[Dict[str, Any]]:
    """
    Checks PostgreSQL standard embeddings for missing or stale vector content.
    
    Returns list of dicts describing stale standards and reasons.
    """
    active_engine = engine or get_db_engine()
    factory = session_factory or get_session_factory(engine=active_engine)
    session: Session = factory()

    stale_items: List[Dict[str, Any]] = []

    try:
        standards = session.query(StandardModel).all()
        std_dicts = [s.to_dict() for s in standards]

        embeddings = session.query(StandardEmbeddingModel).filter(
            StandardEmbeddingModel.embedding_model == embedding_model
        ).all()

        emb_map = {e.standard_id: e for e in embeddings}

        for std in std_dicts:
            std_id = std["id"]
            expected_content = build_embedding_content(std)
            if not expected_content:
                continue

            if std_id not in emb_map:
                stale_items.append({
                    "standard_id": std_id,
                    "reason": "missing_embedding",
                    "details": f"No embedding record found for model '{embedding_model}'"
                })
            else:
                emb_orm = emb_map[std_id]
                if emb_orm.content != expected_content:
                    stale_items.append({
                        "standard_id": std_id,
                        "reason": "stale_content",
                        "details": f"Embedding content mismatch for standard '{std_id}'"
                    })

        return stale_items
    except Exception as e:
        logger.error(f"Error checking embedding staleness: {e}")
        raise
    finally:
        session.close()


def compare_corpora(
    json_path: Optional[str] = None,
    engine: Optional[Any] = None,
    session_factory: Optional[Any] = None,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
) -> Dict[str, Any]:
    """
    Compares the JSON reference corpus against the PostgreSQL database corpus.
    Produces a deterministic comparison report without mutating any data.
    """
    # 1. Load JSON records
    json_records_objs = load_standards_from_json(json_path)
    json_records = [r.model_dump() for r in json_records_objs]
    json_map = {r["id"]: r for r in json_records}

    # 2. Load PostgreSQL records
    pg_records = load_standards_from_postgres(engine=engine, session_factory=session_factory)
    pg_map = {r["id"]: r for r in pg_records}

    json_ids = set(json_map.keys())
    pg_ids = set(pg_map.keys())

    missing_in_pg = sorted(list(json_ids - pg_ids))
    extra_in_pg = sorted(list(pg_ids - json_ids))
    common_ids = sorted(list(json_ids & pg_ids))

    identical_ids: List[str] = []
    changed_records: List[Dict[str, Any]] = []

    for std_id in common_ids:
        j_rec = json_map[std_id]
        p_rec = pg_map[std_id]
        is_ident, diffs = compare_records(j_rec, p_rec)
        if is_ident:
            identical_ids.append(std_id)
        else:
            changed_records.append({
                "id": std_id,
                "is_number": j_rec.get("is_number"),
                "diffs": diffs
            })

    # 3. Check embedding staleness
    stale_embeddings = check_embedding_staleness(
        engine=engine,
        session_factory=session_factory,
        embedding_model=embedding_model
    )

    # 4. Determine overall status
    if len(pg_records) == 0:
        status = "EMPTY_POSTGRES"
    elif len(missing_in_pg) == 0 and len(extra_in_pg) == 0 and len(changed_records) == 0 and len(stale_embeddings) == 0:
        status = "IN_SYNC"
    else:
        status = "OUT_OF_SYNC"

    report = {
        "json_count": len(json_records),
        "postgres_count": len(pg_records),
        "identical_count": len(identical_ids),
        "missing_in_postgres": missing_in_pg,
        "extra_in_postgres": extra_in_pg,
        "changed_records": changed_records,
        "stale_embeddings": stale_embeddings,
        "synchronization_status": status
    }
    return report


def synchronize_corpora(
    json_path: Optional[str] = None,
    engine: Optional[Any] = None,
    session_factory: Optional[Any] = None,
    delete_extra: bool = False,
    sync_embeddings: bool = True,
    embedding_engine: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Idempotently synchronizes the PostgreSQL standards table and standard_embeddings table
    with the JSON reference corpus.

    Params:
        json_path: Path to JSON corpus file
        engine: Custom SQLAlchemy engine
        session_factory: Custom session factory
        delete_extra: If True, purges DB records that do not exist in JSON
        sync_embeddings: If True, updates/seeds embeddings for synchronized records
        embedding_engine: Optional SemanticEmbeddingEngine instance

    Returns:
        Synchronization execution report dict.
    """
    active_engine = engine or get_db_engine()
    Base.metadata.create_all(bind=active_engine)
    factory = session_factory or get_session_factory(engine=active_engine)

    # 1. Perform initial comparison
    report = compare_corpora(
        json_path=json_path,
        engine=active_engine,
        session_factory=factory
    )

    json_records_objs = load_standards_from_json(json_path)
    json_records = [r.model_dump() for r in json_records_objs]

    session: Session = factory()
    inserted = 0
    updated = 0
    deleted_extra = 0

    try:
        existing_models = {m.id: m for m in session.query(StandardModel).all()}
        json_ids = {r["id"] for r in json_records}

        # Handle extra records deletion ONLY if delete_extra is explicitly True
        if delete_extra:
            extra_ids = set(existing_models.keys()) - json_ids
            for extra_id in extra_ids:
                logger.info(f"delete_extra=True: Removing extra PostgreSQL standard '{extra_id}'.")
                session.query(StandardModel).filter(StandardModel.id == extra_id).delete()
                deleted_extra += 1
                existing_models.pop(extra_id, None)

        # Upsert missing and changed records
        for record_obj in json_records_objs:
            rec_dict = record_obj.model_dump()
            rec_id = rec_dict["id"]

            if rec_id in existing_models:
                existing_orm = existing_models[rec_id]
                is_ident, diffs = compare_records(rec_dict, existing_orm.to_dict())
                if not is_ident:
                    # Content updated
                    existing_orm.is_number = rec_dict["is_number"]
                    existing_orm.title = rec_dict["title"]
                    existing_orm.scope = rec_dict["scope"]
                    existing_orm.sector = rec_dict["sector"]
                    existing_orm.product_category = rec_dict["product_category"]
                    existing_orm.keywords = rec_dict.get("keywords", [])
                    existing_orm.revision_year = rec_dict.get("revision_year")
                    existing_orm.status = rec_dict.get("status", "Active (DEMO / SAMPLE DATA)")
                    existing_orm.source_url = rec_dict.get("source_url")
                    existing_orm.description = rec_dict.get("description")
                    existing_orm.amendments = rec_dict.get("amendments", [])
                    existing_orm.related_standards = rec_dict.get("related_standards", [])
                    updated += 1

                    # If text content for embedding changed, delete old stale embedding for this standard
                    old_content = build_embedding_content(existing_orm.to_dict())
                    new_content = build_embedding_content(rec_dict)
                    if old_content != new_content:
                        logger.info(f"Invalidating stale embedding for standard '{rec_id}' due to text content change.")
                        session.query(StandardEmbeddingModel).filter(
                            StandardEmbeddingModel.standard_id == rec_id
                        ).delete()
            else:
                # Create new ORM record
                new_orm = StandardModel.from_pydantic(record_obj)
                session.add(new_orm)
                existing_models[rec_id] = new_orm
                inserted += 1

        session.commit()

        # 2. Synchronize embeddings if requested
        embeddings_summary = {}
        if sync_embeddings:
            logger.info("Synchronizing standard_embeddings table...")
            embeddings_summary = seed_embeddings(
                standards=json_records,
                engine=active_engine,
                session_factory=factory,
                embedding_engine=embedding_engine
            )

        final_pg_count = session.query(StandardModel).count()

        sync_result = {
            "json_count": len(json_records),
            "initial_postgres_count": report["postgres_count"],
            "final_postgres_count": final_pg_count,
            "inserted": inserted,
            "updated": updated,
            "deleted_extra": deleted_extra,
            "embeddings_summary": embeddings_summary,
            "status": "SUCCESS"
        }
        logger.info(f"Corpus synchronization complete: {sync_result}")
        return sync_result

    except Exception as e:
        logger.error(f"Error during corpus synchronization. Rolling back: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="SIH26108 JSON ↔ PostgreSQL Corpus Migration & Synchronization CLI")
    parser.add_argument("--compare", action="store_true", help="Perform read-only comparison report between JSON and PostgreSQL")
    parser.add_argument("--sync", action="store_true", help="Synchronize PostgreSQL corpus with JSON reference baseline")
    parser.add_argument("--json-path", type=str, default=None, help="Custom path to standards JSON file")
    parser.add_argument("--delete-extra", action="store_true", help="Purge extra records in PostgreSQL that do not exist in JSON during sync")
    parser.add_argument("--no-embeddings", action="store_true", help="Skip embedding synchronization during --sync")
    parser.add_argument("--embedding-model", type=str, default=DEFAULT_EMBEDDING_MODEL, help="Embedding model name for staleness check")

    args = parser.parse_args()

    do_sync = args.sync
    do_compare = args.compare or not do_sync

    logger.info("Executing database migration/synchronization CLI...")
    try:
        engine = get_db_engine()
        if not check_database_connection(engine):
            logger.error(f"Database connection to '{DATABASE_URL}' failed. Operation aborted.")
            print(f"ERROR: Database connection to '{DATABASE_URL}' failed. Ensure PostgreSQL server is running.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        logger.error(f"Database connection setup failed: {e}")
        print(f"ERROR: Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if do_sync:
            result = synchronize_corpora(
                json_path=args.json_path,
                engine=engine,
                delete_extra=args.delete_extra,
                sync_embeddings=not args.no_embeddings
            )
            print(f"SUCCESS: Corpus synchronization completed.\n{json.dumps(result, indent=2)}")
        else:
            report = compare_corpora(
                json_path=args.json_path,
                engine=engine,
                embedding_model=args.embedding_model
            )
            print(f"SUCCESS: Corpus comparison completed.\n{json.dumps(report, indent=2)}")
        
        sys.exit(0)
    except Exception as e:
        logger.error(f"Migration CLI operation failed: {e}", exc_info=True)
        print(f"ERROR: Migration CLI failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
