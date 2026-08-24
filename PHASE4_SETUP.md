# Phase 4 Setup — Operational Intelligence

Phase 4 adds real-time operational events, persistent alerts, explainable root-cause analysis, guided recovery, and transparent health-indicator forecasting.

## Install

Extract the contents of this patch directly into the Project RISING repository root. The new `api/routes/operations.py` file should sit beside `health.py`, `pipeline.py`, and `prediction.py`.

Run:

```powershell
python apply_phase4.py
python -m pytest tests/test_phase4_operations.py -v
python -m pytest --cache-clear
python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` and locate **Phase 4 Operations Intelligence**.

## Endpoints

- `POST /api/v1/operations/events`
- `GET /api/v1/operations/alerts`
- `GET /api/v1/operations/alerts/summary`
- `POST /api/v1/operations/alerts/evaluate`
- `PATCH /api/v1/operations/alerts/{alert_id}/acknowledge`
- `GET /api/v1/operations/incidents/{alert_id}/root-cause`
- `GET /api/v1/operations/forecast`
- `GET /api/v1/operations/readiness`

## Demo

With FastAPI running in another terminal:

```powershell
python demo/run_phase4_demo.py
```

## Responsible use

Root-cause output and forecasts are transparent MVP decision-support signals. They do not diagnose disease, automatically execute destructive recovery, or replace public-health and platform operators.
