from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine


DEFAULT_DATABASE_URL = (
    "postgresql+psycopg2://"
    "rising_user:rising_password@127.0.0.1:55432/project_rising"
)


def get_database_url() -> str:
    """
    Read the warehouse database URL from the environment.
    """
    return os.getenv(
        "DATABASE_URL",
        DEFAULT_DATABASE_URL,
    )


def get_engine(
    database_url: str | None = None,
) -> Engine:
    """
    Build a SQLAlchemy engine for the warehouse.
    """
    return create_engine(
        database_url or get_database_url(),
        pool_pre_ping=True,
    )
