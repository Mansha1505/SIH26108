"""
PostgreSQL / SQLAlchemy Database Foundation Module for SIH26108.

Provides:
- Declarative Base for ORM models
- Environment-driven engine creation and session factory
- Safe lazy initialization that does NOT crash on import when PostgreSQL is offline
- Connection testing utilities
"""

from typing import Generator, Optional, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from backend.config import (
    DATABASE_URL,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_ECHO
)
from backend.utils.logger import get_logger

logger = get_logger("DatabaseConnection")


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.x Declarative Base for ORM models.
    All database entities inherit from this base class.
    """
    pass


# Global singleton references for lazy initialization
_engine: Optional[Any] = None
_session_factory: Optional[sessionmaker] = None


def get_db_engine(database_url: Optional[str] = None, force_new: bool = False):
    """
    Returns an engine instance.
    Uses DATABASE_URL from config if no database_url is provided.
    Does NOT connect to the database at creation time (connections are checked out lazily).
    """
    global _engine
    if _engine is not None and not force_new and database_url is None:
        return _engine

    target_url = database_url or DATABASE_URL

    engine_kwargs: dict = {
        "echo": DB_ECHO,
    }

    # Pass connection pool settings if using PostgreSQL / MySQL
    if target_url.startswith("postgresql") or target_url.startswith("postgres"):
        engine_kwargs.update({
            "pool_size": DB_POOL_SIZE,
            "max_overflow": DB_MAX_OVERFLOW,
            "pool_timeout": DB_POOL_TIMEOUT,
        })
    elif target_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    logger.info(f"Creating SQLAlchemy database engine for URL dialect: {target_url.split('://')[0]}")
    try:
        engine = create_engine(target_url, **engine_kwargs)
    except (ModuleNotFoundError, ImportError) as e:
        logger.warning(f"Database driver missing for URL '{target_url}': {e}")
        raise RuntimeError(f"Database driver not installed for '{target_url}': {e}") from e
    except Exception as e:
        logger.warning(f"Failed to create database engine for '{target_url}': {e}")
        raise

    if database_url is None and not force_new:
        _engine = engine

    return engine


def get_session_factory(engine: Optional[Any] = None, force_new: bool = False) -> sessionmaker:
    """
    Returns a SQLAlchemy sessionmaker factory.
    """
    global _session_factory
    if _session_factory is not None and not force_new and engine is None:
        return _session_factory

    active_engine = engine or get_db_engine()
    factory = sessionmaker(autocommit=False, autoflush=False, bind=active_engine)

    if engine is None and not force_new:
        _session_factory = factory

    return factory


def get_db_session(engine: Optional[Any] = None) -> Generator[Session, None, None]:
    """
    FastAPI dependency / generator yielding a database session.
    Closes session automatically upon context completion.
    """
    factory = get_session_factory(engine=engine)
    session: Session = factory()
    try:
        yield session
    finally:
        session.close()


def check_database_connection(engine: Optional[Any] = None) -> bool:
    """
    Tests whether the target database server is reachable and active.
    Executes a simple 'SELECT 1' query.
    Returns True if connected, False if unreachable or missing driver (without raising unhandled exceptions).
    """
    try:
        active_engine = engine or get_db_engine()
        with active_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection test SUCCESSFUL.")
        return True
    except (SQLAlchemyError, RuntimeError, ModuleNotFoundError, ImportError, Exception) as e:
        logger.warning(f"Database connection test FAILED (PostgreSQL may be offline, driver missing, or URL misconfigured): {e}")
        return False

