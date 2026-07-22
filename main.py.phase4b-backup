from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import API_VERSION

# Original Project RISING API routes.
# These routers receive /api/v1 from main.py.
from api.routes.climate import router as climate_router
from api.routes.health import router as base_health_router
from api.routes.pipeline import router as pipeline_router
from api.routes.prediction import router as prediction_router

# Phase 3 Health Intelligence routes.
# These routers already contain their own /api/v1 prefixes.
from api.routers.health import router as health_intelligence_router
from api.routers.intelligence import router as intelligence_router
from api.routers.monitoring import router as monitoring_router

# Phase 4 Operations Intelligence routes.
# This router already contains its own operations prefix.
from api.routes.operations import router as operations_router


app = FastAPI(
    title="Project RISING",
    description=(
        "ASEAN health intelligence, climate resilience, disease-risk "
        "analysis, operational alerting, root-cause analysis, and forecasting."
    ),
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Original API routes
# These routers need /api/v1 added here.
# -------------------------------------------------------------------

app.include_router(
    climate_router,
    prefix="/api/v1",
)

app.include_router(
    base_health_router,
    prefix="/api/v1",
)

app.include_router(
    pipeline_router,
    prefix="/api/v1",
)

app.include_router(
    prediction_router,
    prefix="/api/v1",
)


# -------------------------------------------------------------------
# Phase 3 Health Intelligence
# Do not add another /api/v1 prefix here.
# -------------------------------------------------------------------

app.include_router(health_intelligence_router)
app.include_router(intelligence_router)
app.include_router(monitoring_router)


# -------------------------------------------------------------------
# Phase 4 Operations Intelligence
# Do not add another prefix here.
# -------------------------------------------------------------------

app.include_router(operations_router)


# -------------------------------------------------------------------
# System endpoints
# -------------------------------------------------------------------

@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "project": "Project RISING",
        "status": "running",
        "version": API_VERSION,
        "documentation": "/docs",
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "version": API_VERSION,
    }