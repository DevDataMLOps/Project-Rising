# Retention Policy

Project RISING keeps data long enough to support auditability, reproducibility,
and public-health trend analysis.

## Retention Targets

- Raw batch files: retained permanently for reproducibility
- Processed CSV outputs: retained until replaced by warehouse tables
- Warehouse facts and dimensions: retained permanently for historical analysis
- Streaming accepted events: retained for at least 12 months
- Retry records: retained for 30 days after successful replay
- DLQ records: retained for 12 months or until reviewed and resolved
- Pipeline metrics: retained for 24 months

## Deletion Rules

Deletion must not remove the only copy of a raw source, accepted observation,
or unresolved DLQ event. Any cleanup job must preserve run IDs, checksums, and
resolution notes.
