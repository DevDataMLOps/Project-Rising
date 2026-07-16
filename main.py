from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.climate import router as climate_router
from api.routes.health import router as health_router
from api.routes.pipeline import router as pipeline_router
from api.routes.prediction import router as prediction_router
from api.routes.risk import router as risk_router


app = FastAPI(
    title="Project RISING API",
    description=(
        "Climate-resilient healthcare intelligence platform for ASEAN."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health_router,
    prefix="/api/v1",
)

app.include_router(
    climate_router,
    prefix="/api/v1",
)

app.include_router(
    pipeline_router,
    prefix="/api/v1",
)

app.include_router(
    risk_router,
    prefix="/api/v1",
)

app.include_router(
    prediction_router,
    prefix="/api/v1",
)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "project": "Project RISING",
        "status": "running",
        "version": "2.0.0",
        "description": (
            "Climate-resilient healthcare intelligence platform"
        ),
        "docs": "/docs",
    }


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "Project RISING API",
    }
