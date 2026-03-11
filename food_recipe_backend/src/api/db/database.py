from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.core.config import Settings

_SessionLocal = None
_engine = None


# PUBLIC_INTERFACE
def init_db(settings: Settings) -> None:
    """Initialize the database engine and session factory.

    Contract:
      - Inputs: settings.database_url
      - Outputs: global engine + Session factory configured
      - Errors: SQLAlchemy engine creation errors bubble up
      - Side effects: creates engine; no schema creation here
    """
    global _engine, _SessionLocal
    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        # Needed for SQLite with FastAPI (threaded)
        connect_args = {"check_same_thread": False}

    _engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine, future=True)


# PUBLIC_INTERFACE
def get_engine():
    """Return the initialized SQLAlchemy engine."""
    if _engine is None:
        raise RuntimeError("DB engine not initialized. Call init_db(settings) at startup.")
    return _engine


# PUBLIC_INTERFACE
def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a request-scoped SQLAlchemy Session.

    Contract:
      - Yields: Session
      - Side effects: commits on normal completion, rolls back on exception
      - Errors: re-raises exceptions after rollback
    """
    if _SessionLocal is None:
        raise RuntimeError("DB session factory not initialized. Call init_db(settings) at startup.")

    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Utility context manager for non-request DB usage."""
    if _SessionLocal is None:
        raise RuntimeError("DB session factory not initialized. Call init_db(settings) at startup.")
    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
