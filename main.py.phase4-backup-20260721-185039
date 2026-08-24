from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.climate import router as climate_router
from api.routes.health import router as health_router
from api.routes.pipeline import router as pipeline_router
from api.routes.prediction import router as prediction_router
from api.routes.risk import router as risk_router
from api.config import API_VERSION
from api.routers.health import router as health_router
from api.routers.intelligence import router as intelligence_router
from api.routers.monitoring import router as monitoring_router


app = FastAPI(
    title="Project RISING Health Intelligence API",
    description=(
        "ASEAN health intelligence, risk scoring, anomaly detection, "
        "data-quality monitoring, and climate-health decision support."
    ),
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
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
app.include_router(health_router)
app.include_router(intelligence_router)
app.include_router(monitoring_router)


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
