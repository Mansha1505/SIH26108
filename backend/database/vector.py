"""
pgvector Infrastructure & Extension Capability Module for SIH26108 (Phase 10B).

Provides SQLAlchemy vector integration type reference and database extension capability verification.
Pure infrastructure layer: does NOT perform retrieval, generate embeddings, or alter recommendation logic.
"""

from typing import Dict, Any, Optional
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.database.connection import get_db_engine, check_database_connection
from backend.config import VECTOR_BACKEND, DATABASE_URL
from backend.utils.logger import get_logger

logger = get_logger("PgvectorFoundation")

# Expose official SQLAlchemy Vector type if pgvector library is available
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_PACKAGE_INSTALLED = True
except (ImportError, ModuleNotFoundError):
    Vector = None  # type: ignore
    PGVECTOR_PACKAGE_INSTALLED = False


def is_pgvector_package_available() -> bool:
    """Returns True if the Python `pgvector` package is installed and importable."""
    return PGVECTOR_PACKAGE_INSTALLED


import os

def get_active_vector_backend(vector_backend: Optional[str] = None) -> str:
    """
    Returns the active vector store backend name based on configuration or explicit override.
    Defaults to 'faiss'.
    """
    target = vector_backend or os.getenv("VECTOR_BACKEND", VECTOR_BACKEND)
    return str(target).strip().lower()



def check_pgvector_extension(engine: Optional[Any] = None) -> Dict[str, Any]:
    """
    Checks whether PostgreSQL server is reachable and whether the 'vector' extension is installed.

    Returns structured dictionary:
        {
            "postgres_available": bool,
            "pgvector_available": bool,
            "pgvector_package_installed": bool,
            "active_backend": str,
            "details": str
        }
    
    Will NOT execute 'CREATE EXTENSION vector' automatically.
    """
    active_backend = get_active_vector_backend()
    pkg_installed = is_pgvector_package_available()

    try:
        active_engine = engine or get_db_engine()
        
        # 1. Test basic database connectivity
        if not check_database_connection(active_engine):
            return {
                "postgres_available": False,
                "pgvector_available": False,
                "pgvector_package_installed": pkg_installed,
                "active_backend": active_backend,
                "details": "PostgreSQL database server is unreachable or connection failed."
            }

        # 2. Query PostgreSQL pg_extension table for 'vector'
        with active_engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).fetchone()
            if result:
                logger.info("PostgreSQL 'vector' extension is installed and available.")
                return {
                    "postgres_available": True,
                    "pgvector_available": True,
                    "pgvector_package_installed": pkg_installed,
                    "active_backend": active_backend,
                    "details": "PostgreSQL server is reachable and 'vector' extension is installed."
                }
            else:
                logger.warning("PostgreSQL server is reachable, but 'vector' extension is not installed.")
                return {
                    "postgres_available": True,
                    "pgvector_available": False,
                    "pgvector_package_installed": pkg_installed,
                    "active_backend": active_backend,
                    "details": "PostgreSQL server is reachable, but 'vector' extension is not installed."
                }

    except Exception as e:
        logger.warning(f"Error checking pgvector extension status: {e}")
        return {
            "postgres_available": False,
            "pgvector_available": False,
            "pgvector_package_installed": pkg_installed,
            "active_backend": active_backend,
            "details": f"Failed to check extension status: {e}"
        }
