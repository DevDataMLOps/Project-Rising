from __future__ import annotations

import logging
import uuid
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.logging import configure_logging
from api.observability import metrics
from api.routes.climate import router as climate_router
from api.routes.health import router as health_router
from api.routes.pipeline import router as pipeline_router
from api.routes.prediction import router as prediction_router
from api.routes.risk import router as risk_router
from api.security import verify_api_key
from config.config import Settings, get_settings
from warehouse.db import check_database


logger = logging.getLogger("rising.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime = settings or get_settings()
    configure_logging(runtime.log_level, runtime.log_json)

    application = FastAPI(
        title="Project RISING API",
        description=(
            "Pilot-grade climate-resilient healthcare intelligence platform "
            "for ASEAN decision support. Not a clinical decision system."
        ),
        version=runtime.app_version,
    )

    application.state.settings = runtime
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(runtime.trusted_hosts),
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Accept", "Content-Type", "X-API-Key", "X-Request-ID"],
    )

    @application.middleware("http")
    async def request_controls(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = perf_counter()
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                oversized = int(content_length) > runtime.max_request_body_bytes
            except ValueError:
                oversized = True
            if oversized:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "payload_too_large",
                        "message": "Request body exceeds the configured limit",
                        "request_id": request_id,
                    },
                )

        if request.method in {"POST", "PUT", "PATCH"}:
            body = await request.body()
            if len(body) > runtime.max_request_body_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "payload_too_large",
                        "message": "Request body exceeds the configured limit",
                        "request_id": request_id,
                    },
                )

        response = await call_next(request)
        duration = perf_counter() - started
        metrics.observe(request.method, request.url.path, response.status_code, duration)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        if runtime.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "environment": runtime.environment,
            },
        )
        return response

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "request_id": getattr(request.state, "request_id", None),
            },
            headers=exc.headers,
        )

    @application.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception):
        logger.exception(
            "unhandled_request_error",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    application.include_router(health_router, prefix="/api/v1")
    application.include_router(climate_router, prefix="/api/v1")
    application.include_router(pipeline_router, prefix="/api/v1")
    application.include_router(risk_router, prefix="/api/v1")
    application.include_router(prediction_router, prefix="/api/v1")

    @application.get("/", tags=["System"])
    def root() -> dict[str, str]:
        return {
            "project": "Project RISING",
            "status": "running",
            "version": runtime.app_version,
            "maturity": "production-ready pilot",
            "description": "Climate-resilient healthcare decision-support platform",
            "docs": "/docs",
        }

    @application.get("/health", tags=["System"])
    def health() -> dict[str, str]:
        """Liveness probe: the API process can serve requests."""
        return {"status": "healthy", "service": runtime.app_name}

    @application.get("/ready", tags=["System"])
    def readiness():
        """Readiness probe: required data and configured dependencies work."""
        database_check = (
            check_database(
                required=runtime.database_required,
                database_url=runtime.database_url.get_secret_value(),
            )
            if runtime.database_url
            else {
                "status": "fail" if runtime.database_required else "not_configured",
                "required": runtime.database_required,
            }
        )
        checks = {
            "health_dataset": {
                "status": "pass" if runtime.health_dataset.is_file() else "fail",
                "required": True,
            },
            "database": database_check,
        }
        ready = all(
            check["status"] in {"pass", "not_configured"}
            for check in checks.values()
        )
        payload = {"status": "ready" if ready else "not_ready", "checks": checks}
        return JSONResponse(status_code=200 if ready else 503, content=payload)

    @application.get("/metrics", tags=["System"])
    def prometheus_metrics(_: None = Depends(verify_api_key)):
        if not runtime.metrics_enabled:
            raise HTTPException(status_code=404, detail="Metrics are disabled")
        return PlainTextResponse(metrics.render(), media_type="text/plain; version=0.0.4")

    return application


app = create_app()
