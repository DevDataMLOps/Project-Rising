# Phase 4B — AI & Machine Learning Setup

Phase 4B adds trained, versioned machine-learning models to Project RISING while preserving the platform's responsible-use boundary: aggregate public-health decision support, not clinical diagnosis.

## Models

1. **Random Forest health-indicator forecasting**
   - Trains on country/indicator annual histories.
   - Uses lag values, rolling statistics, year, country, and indicator features.
   - Evaluates on the latest held-out observation of every eligible series.
   - Reports MAE, RMSE, R², and feature importance.

2. **Isolation Forest anomaly detection**
   - Trains without labels on normalized indicator values and annual changes.
   - Returns an anomaly score, review level, and evidence.
   - It flags statistically unusual records for investigation; it does not prove an outbreak or corrupted data.

## Install

Copy the patch contents into the root `project-rising` folder, then run:

```powershell
python apply_phase4b.py
python -m pip install -r requirements.txt
python -m ml.train_all
```

Model artifacts are created under:

```text
models/phase4b/
├── forecast_model.joblib
├── anomaly_model.joblib
├── registry.json
└── training_report.json
```

## Test

```powershell
python -m pytest tests/test_phase4b_ml.py -v
python -m pytest --cache-clear
```

## Start the API

```powershell
python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` and find **Phase 4B AI & Machine Learning**.

## Endpoints

```text
GET  /api/v1/ml/readiness
GET  /api/v1/ml/models
GET  /api/v1/ml/training-report
POST /api/v1/ml/forecast
POST /api/v1/ml/anomaly/predict
GET  /api/v1/ml/drift
```

## Suggested Swagger tests

Forecast:

```json
{
  "country": "Philippines",
  "indicator": "life_expentancy_rate",
  "horizon_years": 3
}
```

Use `GET /api/v1/health-indicators/indicators` to copy the exact indicator spelling available in your processed dataset.

Anomaly review:

```json
{
  "country": "Philippines",
  "indicator": "infant_mortality_rate",
  "year": 2025,
  "value": 150,
  "previous_value": 18
}
```

## Retraining

Run this after the processed health dataset changes:

```powershell
python -m ml.train_all
```

Then check:

```text
GET /api/v1/ml/drift
GET /api/v1/ml/models
```

## Responsible use

- Models use aggregated annual public-health indicators.
- The repository has no validated outbreak labels, so Phase 4B does not claim outbreak-probability accuracy.
- Forecasts estimate indicator values, not individual outcomes.
- Anomaly flags require source, unit, lineage, and public-health review.
