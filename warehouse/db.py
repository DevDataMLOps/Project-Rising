from __future__ import annotations

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from config.config import get_settings


def get_database_url() -> str:
    """Return the configured URL without embedding development credentials."""
    configured = get_settings().database_url
    if configured is None:
        raise RuntimeError("DATABASE_URL is not configured")
    return configured.get_secret_value()


def get_engine(database_url: str | None = None) -> Engine:
    settings = get_settings()
    url = database_url or get_database_url()
    connect_args = {}
    if url.startswith("postgresql"):
        connect_args["connect_timeout"] = settings.database_connect_timeout_seconds
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args=connect_args,
    )


def check_database(
    required: bool = False,
    database_url: str | None = None,
) -> dict[str, object]:
    """Check the optional database without exposing connection details."""
    settings = get_settings()
    configured_url = database_url or (
        settings.database_url.get_secret_value() if settings.database_url else None
    )
    if configured_url is None:
        return {
            "status": "fail" if required else "not_configured",
            "required": required,
        }
    try:
        engine = get_engine(configured_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        return {"status": "pass", "required": required}
    except SQLAlchemyError:
        return {"status": "fail", "required": required}
