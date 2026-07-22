## Phase 4B — Trained AI & Machine Learning

Project RISING now includes two trained and versioned models:

- A Random Forest regressor for annual ASEAN health-indicator forecasting.
- An Isolation Forest for unsupervised detection of unusual indicator records.

The training pipeline records dataset lineage hashes, time-based holdout metrics, model versions, feature importance, artifact paths, and drift baselines. Models can be retrained with `python -m ml.train_all` and served through `/api/v1/ml/*` FastAPI endpoints.

These are aggregate public-health decision-support models. They are not clinically validated, do not use patient-level data, and do not claim outbreak probability without labeled outbreak outcomes.
