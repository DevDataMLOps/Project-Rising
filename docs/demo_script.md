# Project RISING: 3–5 Minute Demo Script

Target runtime: **4 minutes**. Keep the API, Swagger UI, Streamlit dashboard, and terminal ready before recording.

## 0:00–0:30 — The Stakes

**Show:** Title slide or README hero.

**Say:**

> Imagine a typhoon disrupts connectivity in the Philippines while hospitals and public-health teams are still collecting critical records. In a fragile system, records arrive late, duplicate, become malformed, or disappear. Project RISING keeps trusted health data moving through disruption and turns it into explainable decision support.

## 0:30–1:05 — Architecture

**Show:** The end-to-end Mermaid diagram in the README.

**Say:**

> Historical ASEAN health data enters our batch ETL while climate events enter the streaming path. Every record is validated. Invalid data moves to a Dead Letter Queue, temporary failures are buffered and retried, and checkpoints prevent duplicates. Trusted data then feeds our API, dashboard, and climate-health risk model.

## 1:05–1:55 — Resilience Proof

**Show:** Terminal. Run:

```bash
python demo/run_streaming_demo.py
```

**Point to:** normal acceptance, duplicate rejection, DLQ routing, simulated outage, and recovery.

**Say:**

> This is an end-to-end failure scenario, not a static mockup. A valid event is accepted, a duplicate is blocked, a malformed event is quarantined, and an event interrupted by the simulated outage is recovered when connectivity returns. No bad record crosses the trusted-data boundary.

## 1:55–2:55 — Interactive Prediction

**Show:** Streamlit at `http://localhost:8501`.

Use the default scenario:

- Country: Philippines
- Disease: dengue
- Temperature: 29°C
- Rainfall: 180 mm
- Humidity: 85%

Click **Calculate disease risk**.

**Say:**

> The decision-support panel combines this weather scenario with the latest available country health indicators. It returns a 14-day risk level, a climate-suitability score, historical vulnerability, the evidence years and values, and concrete preparedness actions. The method is deterministic and fully explainable; we clearly state that it is a hackathon preparedness estimate, not a clinical forecast.

Change rainfall to `10` and humidity to `55`, then calculate again.

**Say:**

> In the drier scenario the score falls. That behavior is also covered by an automated test, so the demonstration is repeatable.

## 2:55–3:30 — API and Real Output

**Show:** Swagger UI at `http://127.0.0.1:8000/docs`.

Expand `GET /api/v1/disease-risk/sample`, click **Try it out**, then **Execute**.

**Say:**

> The same capability is available as a documented API with a ready-to-run sample. Partners can also post their own country and climate inputs. This is real computed output from the repository, not a screenshot or hard-coded response.

## 3:30–4:00 — Impact and Close

**Show:** Dashboard operational metrics or README requirement mapping.

**Say:**

> Project RISING connects reliable ingestion to a usable public-health action. It aligns with SDG 3 for health, SDG 9 for resilient infrastructure, SDG 13 for climate action, and SDG 17 for interoperable partnerships. The dashboard is the visible layer; the resilient, governed pipeline beneath it is what makes the insight trustworthy.

**Close with:**

> Project RISING protects public-health intelligence when climate disruption makes normal systems unreliable—so teams can recover data, understand risk, and act sooner.

## 3-Minute Cut

To shorten the demo, skip changing the weather scenario and show only the default prediction. Keep the resilience run, prediction output, and closing.

## 5-Minute Extension

Use the extra minute to show `accepted_weather_events.jsonl`, `weather_events_dlq.jsonl`, and `checkpoints.txt`, or query the optional PostgreSQL `fact_weather_observation` table.
