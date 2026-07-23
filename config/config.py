from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, model_validator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    )


class Settings(BaseModel):
    """Validated runtime configuration loaded from environment variables."""

    app_name: str = "Project RISING API"
    app_version: str = "2.0.0"
    environment: Literal["development", "test", "staging", "production"] = (
        "development"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = True
    api_key: SecretStr | None = None
    require_api_key: bool = False
    cors_origins: tuple[str, ...] = ("http://localhost:8501",)
    trusted_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "testserver")
    metrics_enabled: bool = True
    max_request_body_bytes: int = Field(default=1_048_576, ge=1_024, le=10_485_760)
    health_dataset: Path = PROJECT_ROOT / "data/processed/asean_health_indicators.csv"
    database_url: SecretStr | None = None
    database_required: bool = False
    database_connect_timeout_seconds: int = Field(default=5, ge=1, le=30)
    database_max_retries: int = Field(default=3, ge=0, le=10)

    @model_validator(mode="after")
    def validate_secure_configuration(self) -> "Settings":
        if self.require_api_key and not self.api_key:
            raise ValueError("API_KEY is required when REQUIRE_API_KEY=true")
        if (
            self.require_api_key
            and self.api_key
            and len(self.api_key.get_secret_value()) < 16
        ):
            raise ValueError("API_KEY must contain at least 16 characters")
        if self.database_required and not self.database_url:
            raise ValueError("DATABASE_URL is required when DATABASE_REQUIRED=true")
        if self.environment == "production" and "*" in self.cors_origins:
            raise ValueError("Wildcard CORS origins are not allowed in production")
        return self

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "Project RISING API"),
            app_version=os.getenv("APP_VERSION", "2.0.0"),
            environment=os.getenv("APP_ENV", "development").lower(),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            log_json=_boolean("LOG_JSON", True),
            api_key=os.getenv("API_KEY") or None,
            require_api_key=_boolean("REQUIRE_API_KEY", False),
            cors_origins=_csv("CORS_ORIGINS", "http://localhost:8501"),
            trusted_hosts=_csv(
                "TRUSTED_HOSTS", "localhost,127.0.0.1,testserver"
            ),
            metrics_enabled=_boolean("METRICS_ENABLED", True),
            max_request_body_bytes=int(os.getenv("MAX_REQUEST_BODY_BYTES", "1048576")),
            health_dataset=Path(
                os.getenv(
                    "HEALTH_DATASET",
                    str(PROJECT_ROOT / "data/processed/asean_health_indicators.csv"),
                )
            ),
            database_url=os.getenv("DATABASE_URL") or None,
            database_required=_boolean("DATABASE_REQUIRED", False),
            database_connect_timeout_seconds=int(
                os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "5")
            ),
            database_max_retries=int(os.getenv("DATABASE_MAX_RETRIES", "3")),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_environment()
