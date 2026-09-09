"""
Corpus Seeding and Migration Utility for SIH26108 Standards Intelligence.

Loads, validates, and populates the Indian Standards database from backend/data/standards.json.
Provides idempotent upsert functionality, atomic transaction management, and explicit CLI execution.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.database.connection import (
    Base,
    get_db_engine,
    get_session_factory,
    check_database_connection
)
from backend.database.models import StandardModel
from backend.models.schemas import IndianStandardRecord
from backend.config import DATABASE_URL
from backend.utils.logger import get_logger

logger = get_logger("DatabaseSeed")


def load_standards_from_json(json_path: Optional[str] = None) -> List[IndianStandardRecord]:
    """
    Reads and validates the standards corpus JSON file.
    
    Returns a list of validated IndianStandardRecord Pydantic domain models.
    Raises FileNotFoundError, ValueError, or pydantic.ValidationError on invalid input.
    """
    if json_path is None:
        base_dir = Path(__file__).resolve().parent.parent
        json_path = base_dir / "data" / "standards.json"

    p = Path(json_path)
    if not p.exists():
        logger.error(f"Standards JSON corpus file missing at: {p}")
        raise FileNotFoundError(f"Standards file missing: {p}")

    logger.info(f"Loading standards JSON corpus from: {p}")
    with open(p, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if not isinstance(raw_data, list):
        logger.error(f"Corpus JSON file {p} does not contain a JSON array.")
        raise ValueError(f"Corpus JSON file at {p} must contain a list of objects.")

    validated_records: List[IndianStandardRecord] = []
    for idx, item in enumerate(raw_data):
        if not isinstance(item, dict):
            logger.error(f"Item at index {idx} in {p} is not a dict object.")
            raise ValueError(f"Corpus item at index {idx} must be a dictionary.")

        # Ensure unique id if missing
        if not item.get("id"):
            is_clean = item.get("is_number", f"IS-{idx}").replace(" ", "-").replace(":", "-").replace("/", "-")
            item["id"] = is_clean

        # Enforce DEMO data flag
        if "status" in item and "DEMO" not in item["status"]:
            item["status"] = f"{item['status']} (DEMO / SAMPLE DATA)"

        record = IndianStandardRecord(**item)
        validated_records.append(record)

    logger.info(f"Successfully loaded and validated {len(validated_records)} standard records from {p}.")
    return validated_records


def seed_standards(
    json_path: Optional[str] = None,
    engine: Optional[Any] = None,
    session_factory: Optional[Any] = None,
    clear_existing: bool = False
) -> Dict[str, Any]:
    """
    Seeds standards corpus into the database in an idempotent transaction.
    
    Params:
        json_path: Path to standards JSON file (defaults to backend/data/standards.json)
        engine: SQLAlchemy engine to use
        session_factory: Custom session factory (e.g. for testing)
        clear_existing: If True, purges all existing records before seeding

    Returns:
        Dict containing seed statistics (inserted, updated, total_processed, total_in_db)
    """
    active_engine = engine or get_db_engine()
    
    # Ensure tables exist
    Base.metadata.create_all(bind=active_engine)

    factory = session_factory or get_session_factory(engine=active_engine)
    
    # 1. Load and validate input corpus
    records = load_standards_from_json(json_path)

    session: Session = factory()
    inserted = 0
    updated = 0

    try:
        if clear_existing:
            logger.warning("clear_existing=True specified: purging all existing standards from database.")
            session.query(StandardModel).delete()
            session.flush()

        # Fetch existing records indexed by ID for fast idempotent lookup
        existing_models = {m.id: m for m in session.query(StandardModel).all()}

        for record in records:
            rec_dict = record.model_dump()
            rec_id = rec_dict["id"]

            if rec_id in existing_models:
                # Update existing ORM record
                existing_orm = existing_models[rec_id]
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
            else:
                # Create new ORM record
                new_orm = StandardModel.from_pydantic(record)
                session.add(new_orm)
                existing_models[rec_id] = new_orm
                inserted += 1

        # Commit transaction atomically
        session.commit()
        total_in_db = session.query(StandardModel).count()

        stats = {
            "total_processed": len(records),
            "inserted": inserted,
            "updated": updated,
            "total_in_db": total_in_db
        }
        logger.info(f"Database standards seeding complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error during standards database seeding. Rolling back transaction: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def clear_standards(engine: Optional[Any] = None, session_factory: Optional[Any] = None) -> int:
    """
    Explicitly purges all standards from the standards table.
    
    Returns the count of deleted rows.
    """
    active_engine = engine or get_db_engine()
    factory = session_factory or get_session_factory(engine=active_engine)
    session: Session = factory()
    try:
        deleted = session.query(StandardModel).delete()
        session.commit()
        logger.info(f"Cleared {deleted} records from standards table.")
        return deleted
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to clear standards table: {e}")
        raise
    finally:
        session.close()


def main():
    """
    CLI Entry point for explicit PostgreSQL standards corpus seeding.
    
    Usage:
        python -m backend.database.seed
    """
    logger.info("Executing database standards corpus seed CLI...")
    engine = get_db_engine()

    # Connection check: fail immediately without fallback if PostgreSQL/DB is unreachable
    if not check_database_connection(engine):
        logger.error(f"Database at {DATABASE_URL} is unreachable. Seeding aborted.")
        print(f"ERROR: Database connection to '{DATABASE_URL}' failed. Ensure PostgreSQL server is running.", file=sys.stderr)
        sys.exit(1)

    try:
        stats = seed_standards(engine=engine)
        print(f"SUCCESS: Standards database seed completed. Stats: {stats}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Seed command failed with error: {e}", exc_info=True)
        print(f"ERROR: Seeding failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
