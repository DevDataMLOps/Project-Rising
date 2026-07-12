# Incident Response

This document defines the operating response when Project RISING ingestion,
validation, or warehouse loading fails.

## Incident Types

- Source file cannot be parsed
- Schema validation failure spike
- Streaming backlog growth
- Retry exhaustion
- Dead-letter queue growth
- Database or network outage
- Duplicate event surge

## Response Steps

1. Identify affected pipeline and source.
2. Check pipeline run status and metrics.
3. Inspect retry output and DLQ payloads.
4. Confirm whether failures are source quality, infrastructure, or code issues.
5. Replay corrected records after validation.
6. Record resolution notes and prevention action.

## Recovery Principles

- Do not delete failed payloads until reviewed.
- Do not manually edit accepted warehouse facts without audit notes.
- Prefer replay from raw, retry, or DLQ sources.
- Preserve event IDs and file checksums for traceability.
