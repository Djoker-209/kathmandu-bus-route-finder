"""
db/session.py

Engine + session factory for the app. Everything that talks to Postgres
(queries.py, API dependency injection, routing graph loader) should get
its Session from `get_db`, not create engines/sessions of its own.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # avoids stale-connection errors after DB restarts
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a Session, always closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()