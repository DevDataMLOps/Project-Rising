# Project RISING

RISING means **Resilient Intelligent Surveillance & Integrated Next-Generation Healthcare**.

Project RISING is a climate-resilient health data engineering platform designed to keep public-health data moving during network failures, disasters, and infrastructure disruptions across ASEAN.

The core promise is simple:

```text
No critical health record should be lost during climate-induced connectivity failures.
```

Instead of focusing only on prediction or dashboards, Project RISING focuses on the reliability layer that public-health systems need before analytics can be trusted: batch ingestion, real-time event processing, validation, retries, idempotency, dead-letter handling, and warehouse synchronization.

## MVP Implementation Status

This repository separates working MVP capabilities from simulated inputs and future production features. The country risk endpoint is a transparent comparative demonstration score, not an AI prediction.

| Capability | Status | Evidence |
|---|---|---|
| Historical health-data ETL | Implemented | [`pipelines/`](pipelines/) |
| Schema and data-quality validation | Implemented | [`schemas/`](schemas/) and [`pipelines/validation/`](pipelines/validation/) |
| Climate-event streaming | Simulated | [`streaming/`](streaming/) and [`demo/run_streaming_demo.py`](demo/run_streaming_demo.py) |
| Retry and outage recovery | Implemented | [`streaming/retry_handler.py`](streaming/retry_handler.py) and [`demo/`](demo/) |
| Dead Letter Queue routing | Implemented | [`streaming/dlq_handler.py`](streaming/dlq_handler.py) |
| Duplicate protection and checkpoints | Implemented | [`streaming/consumer.py`](streaming/consumer.py) and warehouse constraints |
| PostgreSQL warehouse loading | Implemented | [`warehouse/`](warehouse/) and [`sql/`](sql/) |
| Pipeline operations dashboard | Implemented | [`demo/pipeline_operations_dashboard.py`](demo/pipeline_operations_dashboard.py) |
| Public-health and pipeline API | Implemented MVP | [`api/routes/`](api/routes/) and [`main.py`](main.py) |
| Country comparative risk score | Implemented demo (not AI) | [`api/routes/risk.py`](api/routes/risk.py) |
| Automated test workflow | Implemented | [`.github/workflows/tests.yml`](.github/workflows/tests.yml) |
| Live weather-provider integration | Designed | Future production integration |
| Outbreak prediction model | Planned | [`docs/architecture/03_ai_architecture.md`](docs/architecture/03_ai_architecture.md) |
| Patient-level clinical integration | Out of scope for MVP | Future production phase with additional privacy and security controls |

## Problem

Climate events such as typhoons, floods, heatwaves, and rural infrastructure outages can delay or interrupt healthcare data collection. When connectivity fails, critical records may arrive late, duplicate, become malformed, or disappear before analysts and decision-makers can act.

Project RISING addresses this by treating disruption as an expected condition, not an exception.

## Solution

Project RISING combines historical batch health data with simulated real-time climate/weather events in a resilient hybrid pipeline.

```text
CSV Batch Data
       \
        \
Weather Stream
        |
        v
Validation Layer
        |
        v
Retry Mechanism
        |
        v
Idempotency / Checkpoints
        |
   +----+----+
   |         |
Success   Failure
   |         |
   v         v
Warehouse   DLQ
```

Accepted records move into trusted storage and PostgreSQL warehouse tables. Failed or malformed records are isolated in a Dead Letter Queue for review. Duplicate events are protected by checkpoints and warehouse constraints.

## What This Proves

- Historical ASEAN health CSV files can be processed through a governed batch ETL pipeline.
- Real-time weather events can be validated, retried, deduplicated, and recovered after a simulated outage.
- Bad records do not pollute the trusted analytics layer.
- Accepted events can be loaded into PostgreSQL fact and dimension tables.
- The system is reproducible with tests, schemas, governance docs, SQL, and Docker Compose.

## Demo Commands

Run the batch pipeline:

```powershell
py -m pipelines.run_etl
```

Run the streaming resilience demo:

```powershell
py demo\run_streaming_demo.py
```

Open the pipeline operations dashboard:

```powershell
py -m streamlit run demo\pipeline_operations_dashboard.py
```

If Streamlit is not installed yet, install the project dependencies first:

```powershell
py -m pip install -r requirements.txt
```

Run the streaming demo with PostgreSQL warehouse loading:

```powershell
docker compose up -d postgres
py demo\run_streaming_demo.py --load-postgres
```

Inspect loaded warehouse rows:

```powershell
docker compose exec postgres psql -U rising_user -d project_rising -c "SELECT event_id, observed_at, temperature_c, humidity_pct, rainfall_mm FROM fact_weather_observation ORDER BY observed_at DESC LIMIT 10;"
```

Run tests:

```powershell
py -m pytest
```

## Demo Story

Imagine a typhoon disrupts connectivity in the Philippines.

Project RISING receives health and climate-related events while the network is unstable. One record is malformed and is routed to the DLQ. Another record fails during the simulated outage and is marked for retry. When connectivity is restored, the event is recovered and written to accepted storage. Accepted events can then be synchronized into PostgreSQL for analytics.

The message for judges:

```text
The dashboard is not the product. The resilient pipeline is the product.
Project RISING protects public-health data when climate disruption makes normal systems unreliable.
```

## Repository Guide

- `pipelines/`: batch extraction, transformation, validation, loading, and metadata processing.
- `streaming/`: simulated real-time event production, retry handling, checkpointing, and DLQ routing.
- `warehouse/`: PostgreSQL loading utilities for accepted streaming events.
- `schemas/`: data contracts for health and weather records.
- `sql/`: warehouse dimension, fact, and metadata table definitions.
- `demo/`: runnable streaming resilience demo and operations dashboard.
- `docs/architecture/`: system, data flow, AI, security, and climate-resilience architecture notes.
- `docs/governance/`: data contracts, lineage, quality rules, retention, incident response, and SLOs.
- `tests/`: automated tests for ingestion, transformation, validation, schema checks, retries, DLQ, deduplication, and warehouse loading helpers.

## Architecture Documentation

- [System Architecture](docs/architecture/01_system_architecture.md)
- [Data Flow Architecture](docs/architecture/02_data_flow.md)
- [AI Architecture](docs/architecture/03_ai_architecture.md)
- [Security Architecture](docs/architecture/04_security_architecture.md)
- [Climate-Resilience Architecture](docs/architecture/05_climate_resilience.md)

## Elevator Pitch

Project RISING ensures that no public-health data is lost during climate disasters.

Our hybrid data pipeline ingests historical health datasets and real-time climate events, validates every record, retries failed transmissions, guarantees idempotent processing, isolates malformed data in a Dead Letter Queue, and synchronizes accepted records into a warehouse when connectivity is restored.

This enables ASEAN governments to maintain reliable health intelligence even when floods, typhoons, and rural network failures disrupt traditional healthcare systems.
