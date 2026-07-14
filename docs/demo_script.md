# Project RISING Demo Script

RISING means **Resilient Intelligent Surveillance & Integrated Next-Generation Healthcare**.

## Opening

Start with the problem, not the technology.

```text
Imagine a typhoon has disrupted connectivity in the Philippines.
Hospitals and public-health teams are still collecting critical records, but the network is unstable.
In many systems, those records may be delayed, duplicated, malformed, or lost.
Project RISING is designed for that exact moment.
```

## Core Message

```text
Project RISING guarantees that no critical public-health data is lost during climate-induced connectivity failures.
```

Then explain the architecture in one breath:

```text
We combine historical batch health datasets with real-time climate events.
Every record passes through validation, retry handling, idempotency checks, and routing.
Accepted records go to trusted storage and the warehouse.
Failed records go to a Dead Letter Queue for review.
```

## Demo Step 1: Batch Pipeline

Run:

```powershell
py -m pipelines.run_etl
```

Say:

```text
This processes historical ASEAN health datasets into a clean, standardized output.
It represents the batch side of our hybrid ingestion architecture.
```

Show:

```text
data/processed/asean_health_indicators.csv
data/processed/indicator_metadata.csv
```

## Demo Step 2: Streaming Resilience

Run:

```powershell
py demo\run_streaming_demo.py
```

Point out these sections:

```text
1. Generate weather events
2. Process normal event flow
3. Prove duplicate protection
4. Route malformed event to DLQ
5. Simulate network failure and retry
6. Restore connectivity and recover
```

Say:

```text
Here we simulate real-time climate/weather events.
The system accepts valid records, blocks duplicates, sends malformed records to DLQ, and recovers a failed event when connectivity is restored.
```

Show:

```text
data/streaming/accepted_weather_events.jsonl
data/streaming/weather_events_dlq.jsonl
data/streaming/checkpoints.txt
```

Then open the operations dashboard:

```powershell
py -m streamlit run demo\pipeline_operations_dashboard.py
```

If Streamlit is not installed yet:

```powershell
py -m pip install -r requirements.txt
```

Say:

```text
This operations dashboard is not a health dashboard.
It shows the reliability proof points: accepted records, DLQ records, checkpoints, recovery after retry, and warehouse connectivity.
```

## Demo Step 3: Warehouse Loading

Run:

```powershell
docker compose up -d postgres
py demo\run_streaming_demo.py --load-postgres
```

Expected result:

```text
{'input': 6, 'inserted': 6, 'duplicates': 0}
```

Say:

```text
The accepted stream events are now loaded into PostgreSQL fact and dimension tables.
This proves the pipeline can move from local resilience into an analytics-ready warehouse.
```

Inspect the warehouse:

```powershell
docker compose exec postgres psql -U rising_user -d project_rising -c "SELECT event_id, observed_at, temperature_c, humidity_pct, rainfall_mm FROM fact_weather_observation ORDER BY observed_at DESC LIMIT 10;"
```

## What Each Output Proves

`accepted_weather_events.jsonl` proves valid events are preserved.

`weather_events_dlq.jsonl` proves bad records are isolated instead of corrupting trusted data.

`checkpoints.txt` proves duplicate protection.

`fact_weather_observation` proves accepted stream events can be synchronized into a structured warehouse.

## Closing

Use this closing line:

```text
Project RISING is not just a dashboard.
It is a resilient public-health data fabric that keeps collecting, protecting, and synchronizing critical records when climate disruption makes normal systems unreliable.
```

## Short Version

If time is limited, run only:

```powershell
py demo\run_streaming_demo.py
```

Then show:

```text
accepted_weather_events.jsonl
weather_events_dlq.jsonl
checkpoints.txt
```

Say:

```text
This proves zero data loss behavior at the pipeline level: valid data is accepted, invalid data is quarantined, duplicate data is blocked, and failed data is recovered after retry.
```
