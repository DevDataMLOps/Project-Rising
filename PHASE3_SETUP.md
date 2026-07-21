# Phase 3 — Health Intelligence API

This patch upgrades Project RISING from the basic FastAPI health check to a versioned Health Intelligence API.

## Included capabilities

- Health-record filtering and pagination
- ASEAN country and indicator catalogues
- Country health profiles
- Cross-country indicator comparisons
- Historical trend analysis
- Explainable country health-risk scores
- Dengue and malaria climate-health risk estimates
- Historical anomaly detection
- Data-quality, pipeline-status, and readiness endpoints
- Swagger and ReDoc documentation
- Automated API tests

## Install into the repository

Extract this archive and copy its contents into the root of `Project-Rising`. Allow Windows to replace `main.py`.

From PowerShell inside the repository:

```powershell
py -m pip install -r requirements.txt
py -m pipelines.run_etl
py -m pytest
py -m uvicorn main:app --reload
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

## Primary endpoints

```text
GET  /api/v1/health-indicators
GET  /api/v1/health-indicators/countries
GET  /api/v1/health-indicators/indicators
GET  /api/v1/health-indicators/metadata
GET  /api/v1/countries/{country}/profile
GET  /api/v1/health-indicators/compare/{indicator}
GET  /api/v1/health-indicators/trends?country=...&indicator=...
GET  /api/v1/countries/{country}/risk
POST /api/v1/disease-risk/predict
GET  /api/v1/anomalies
GET  /api/v1/data-quality
GET  /api/v1/pipeline/status
GET  /api/v1/readiness
GET  /api/v1/climate-events
```

## Git commands

```powershell
git status
git add main.py api tests/test_phase3_api.py PHASE3_SETUP.md
git commit -m "feat: implement Phase 3 health intelligence API"
git push origin main
```

The processed CSV files in this archive are included only so the patch can be tested immediately. Your ETL pipeline remains the source of truth and can regenerate them.
