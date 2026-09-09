import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import func
from backend.models.schemas import IndianStandardRecord
from backend.database import get_session_factory, StandardModel
from backend.config import REPOSITORY_TYPE
from backend.utils.logger import get_logger

logger = get_logger("StandardsRepository")

class StandardsRepository:
    """
    Abstract Repository interface for Indian Standards data access.
    Decouples the retrieval engines (BM25, Embeddings, Hybrid fusion) from underlying persistence.
    Allows swapping local JSON storage with PostgreSQL + pgvector seamlessly.
    """
    def get_all_standards(self) -> List[Dict[str, Any]]:
        """Retrieves all standard records from persistence."""
        raise NotImplementedError("Subclasses must implement get_all_standards()")

    def get_standard_by_id(self, standard_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single standard by its unique identifier."""
        raise NotImplementedError("Subclasses must implement get_standard_by_id()")

    def get_standard_by_is_number(self, is_number: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single standard by its official IS designation number."""
        raise NotImplementedError("Subclasses must implement get_standard_by_is_number()")


class JsonStandardsRepository(StandardsRepository):
    """
    Local JSON file implementation of StandardsRepository.
    Loads demo dataset from backend/data/standards.json into validated IndianStandardRecord models.
    """
    def __init__(self, json_path: Optional[str] = None):
        if json_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            json_path = base_dir / "data" / "standards.json"
        self.json_path = Path(json_path)
        self._cache: Optional[List[Dict[str, Any]]] = None

    def _load_data(self) -> List[Dict[str, Any]]:
        if self._cache is not None:
            return self._cache

        if not self.json_path.exists():
            logger.error(f"Standards JSON dataset file not found at: {self.json_path}")
            raise FileNotFoundError(f"Standards file missing: {self.json_path}")

        logger.info(f"Loading standards corpus from JSON repository: {self.json_path}")
        with open(self.json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        validated_records = []
        for idx, item in enumerate(raw_data):
            # Ensure unique id if missing
            if not item.get("id"):
                is_clean = item.get("is_number", f"IS-{idx}").replace(" ", "-").replace(":", "-").replace("/", "-")
                item["id"] = is_clean

            # Enforce DEMO data flag
            if "DEMO" not in item.get("status", ""):
                item["status"] = f"{item.get('status', 'Active')} (DEMO / SAMPLE DATA)"

            # Validate against Pydantic schema
            record = IndianStandardRecord(**item)
            validated_records.append(record.model_dump())

        self._cache = validated_records
        logger.info(f"Successfully loaded and validated {len(validated_records)} demo standards records.")
        return self._cache

    def get_all_standards(self) -> List[Dict[str, Any]]:
        return self._load_data()

    def get_standard_by_id(self, standard_id: str) -> Optional[Dict[str, Any]]:
        standards = self.get_all_standards()
        for std in standards:
            if std["id"] == standard_id:
                return std
        return None

    def get_standard_by_is_number(self, is_number: str) -> Optional[Dict[str, Any]]:
        standards = self.get_all_standards()
        clean_target = is_number.strip().lower()
        for std in standards:
            if std["is_number"].strip().lower() == clean_target:
                return std
        return None


class PostgresStandardsRepository(StandardsRepository):
    """
    SQLAlchemy / PostgreSQL implementation of StandardsRepository.
    Loads standard records from relational standards storage and converts them to IndianStandardRecord domain models.
    """
    def __init__(self, session_factory=None, engine=None):
        self.engine = engine
        self._session_factory = session_factory

    def _get_factory(self):
        if self._session_factory:
            return self._session_factory
        return get_session_factory(engine=self.engine)

    def get_all_standards(self) -> List[Dict[str, Any]]:
        """Retrieves all standard records from PostgreSQL/SQLAlchemy DB."""
        factory = self._get_factory()
        try:
            with factory() as session:
                orm_records = session.query(StandardModel).all()
                return [record.to_pydantic().model_dump() for record in orm_records]
        except Exception as e:
            logger.error(f"PostgresStandardsRepository.get_all_standards failed: {e}")
            raise RuntimeError(f"Failed to retrieve standards from PostgreSQL repository: {e}") from e

    def get_standard_by_id(self, standard_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single standard by its unique identifier."""
        factory = self._get_factory()
        try:
            with factory() as session:
                record = session.query(StandardModel).filter(StandardModel.id == standard_id).first()
                if not record:
                    return None
                return record.to_pydantic().model_dump()
        except Exception as e:
            logger.error(f"PostgresStandardsRepository.get_standard_by_id failed for '{standard_id}': {e}")
            raise RuntimeError(f"Failed to retrieve standard '{standard_id}' from PostgreSQL repository: {e}") from e

    def get_standard_by_is_number(self, is_number: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single standard by its official IS designation number."""
        factory = self._get_factory()
        clean_target = is_number.strip().lower()
        try:
            with factory() as session:
                record = session.query(StandardModel).filter(
                    func.lower(StandardModel.is_number) == clean_target
                ).first()
                if not record:
                    # Fallback in-memory scan if case/whitespace normalization varies
                    records = session.query(StandardModel).all()
                    for rec in records:
                        if rec.is_number.strip().lower() == clean_target:
                            return rec.to_pydantic().model_dump()
                    return None
                return record.to_pydantic().model_dump()
        except Exception as e:
            logger.error(f"PostgresStandardsRepository.get_standard_by_is_number failed for '{is_number}': {e}")
            raise RuntimeError(f"Failed to retrieve standard '{is_number}' from PostgreSQL repository: {e}") from e


# Backward compatibility aliases
BaseCorpusLoader = StandardsRepository
JsonCorpusLoader = JsonStandardsRepository

def get_default_repository(repository_type: Optional[str] = None) -> StandardsRepository:
    """
    Factory function returning the active standards repository based on configuration or explicit type override.
    
    Defaults to JsonStandardsRepository baseline if REPOSITORY_TYPE="json" or unconfigured.
    """
    target_type = repository_type or os.getenv("REPOSITORY_TYPE", REPOSITORY_TYPE)
    target_type = str(target_type).strip().lower()

    if target_type in ("postgres", "postgresql"):
        logger.info("Initializing PostgreSQL standards repository...")
        return PostgresStandardsRepository()
    elif target_type == "json":
        logger.info("Initializing JSON standards repository baseline...")
        return JsonStandardsRepository()
    else:
        logger.warning(f"Unknown REPOSITORY_TYPE '{target_type}'. Defaulting to 'json' repository baseline.")
        return JsonStandardsRepository()

def get_default_corpus_loader() -> StandardsRepository:
    """Backward compatibility alias for get_default_repository."""
    return get_default_repository()


