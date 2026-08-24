## Phase 3 — Health Intelligence API

Project RISING exposes validated ASEAN health data through a FastAPI decision-support layer. The API provides country profiles, regional comparisons, historical trends, explainable health-risk scores, dengue and malaria climate-health estimates, anomaly detection, data-quality reporting, pipeline status, and readiness checks.

Run the API:

```powershell
py -m uvicorn main:app --reload
```

Open the interactive documentation at `http://127.0.0.1:8000/docs`.
