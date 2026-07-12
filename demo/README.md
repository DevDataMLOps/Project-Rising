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
