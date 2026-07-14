# Streaming Resilience Demo

This demo shows the fault-tolerant streaming branch of Project RISING.

It demonstrates:

- valid weather event ingestion
- schema validation
- duplicate detection through checkpoints
- retry behavior during a simulated outage
- dead-letter queue routing for permanently failed records

## Run

From the project root:

```powershell
py demo\run_streaming_demo.py
```

To also load accepted events into PostgreSQL:

```powershell
docker compose up -d postgres
py demo\run_streaming_demo.py --load-postgres
```

To open the operations dashboard:

```powershell
py -m streamlit run demo\pipeline_operations_dashboard.py
```

If Streamlit is not installed yet, install the project dependencies first:

```powershell
py -m pip install -r requirements.txt
```

The demo uses this default warehouse connection:

```text
postgresql+psycopg2://rising_user:rising_password@127.0.0.1:55432/project_rising
```

To inspect the loaded warehouse rows:

```powershell
docker compose exec postgres psql -U rising_user -d project_rising -c "SELECT event_id, observed_at, temperature_c, humidity_pct, rainfall_mm FROM fact_weather_observation ORDER BY observed_at DESC LIMIT 10;"
```

If PostgreSQL rejects the password for `rising_user`, the local Docker volume was
probably initialized with older credentials. For demo data, reset the volume and
start Postgres again:

```powershell
docker compose down -v
docker compose up -d postgres
py demo\run_streaming_demo.py --load-postgres
```

## Outputs

The demo writes temporary local outputs under:

```text
data/streaming/
```

Files created:

- `weather_events.jsonl`: generated input events
- `accepted_weather_events.jsonl`: accepted events
- `weather_events_dlq.jsonl`: failed events after retry exhaustion
- `checkpoints.txt`: processed event fingerprints

These outputs are ignored by Git because they are generated demo artifacts.

## Demo Story

1. Generate valid weather events.
2. Process valid events into accepted storage.
3. Reprocess one event to prove duplicate protection.
4. Process a malformed event and show DLQ routing.
5. Simulate network failure and show retry status.
6. Restore normal operation and show successful recovery.
7. Optionally load accepted events into `fact_weather_observation`.
