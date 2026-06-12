from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_DB_PATH = DATA_DIR / "vicinity.db"


def database_url() -> str:
    configured = os.getenv("DATABASE_URL", "").strip()
    if configured.startswith("postgres://"):
        configured = configured.replace("postgres://", "postgresql+psycopg://", 1)
    elif configured.startswith("postgresql://"):
        configured = configured.replace("postgresql://", "postgresql+psycopg://", 1)
    return configured or f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


class Base(DeclarativeBase):
    pass


DATABASE_URL = database_url()
CONNECT_ARGS = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
