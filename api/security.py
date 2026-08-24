from __future__ import annotations

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from config.config import get_settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(provided_key: str | None = Security(api_key_header)) -> None:
    """Require a configured API key for protected pilot operations."""

    settings = get_settings()
    if not settings.require_api_key:
        return

    expected = settings.api_key.get_secret_value() if settings.api_key else ""
    if not provided_key or not secrets.compare_digest(provided_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
