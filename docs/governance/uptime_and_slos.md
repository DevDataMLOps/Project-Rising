# Uptime And SLOs

The MVP defines simple service-level objectives that can be measured from
pipeline run metadata and streaming metrics.

## Batch SLOs

- Batch completion success rate: 99 percent
- Batch freshness: processed data available within 24 hours of source arrival
- Duplicate rate: below 1 percent
- Accepted data loss target: 0 records

## Streaming SLOs

- Event processing latency: under 60 seconds for normal operation
- Retry visibility: retry count and failure reason captured for every failure
- DLQ review time: under 24 hours
- Accepted event loss target: 0 events

## Monitoring Metrics

- Records received
- Records accepted
- Records rejected
- Records routed to DLQ
- Processing latency
- Duplicate count
- Pipeline status

These metrics are stored in `pipeline_metrics` and can be surfaced in a
dashboard.
