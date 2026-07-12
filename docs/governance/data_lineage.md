# Data Lineage

Project RISING separates raw ingestion, validation, warehouse modeling, and
serving layers so every output can be traced back to its source.

## Batch Lineage

```text
raw CSV files
-> data/raw
-> pipelines.extract
-> pipelines.transform
-> pipelines.validate
-> data/processed/asean_health_indicators.csv
-> warehouse fact_health_observation
-> FastAPI and Streamlit consumers
```

## Metadata Lineage

```text
data/raw/SDG3_summary.csv
-> pipelines.metadata
-> data/processed/indicator_metadata.csv
-> dim_indicator
-> dashboard descriptions and source links
```

## Streaming Lineage

```text
weather event producer
-> weather-events topic or JSONL landing file
-> streaming.consumer
-> schema validation
-> idempotency checkpoint
-> accepted weather store or fact_weather_observation
-> retry or dead-letter output when failures occur
```

## Audit Fields

Warehouse and metadata tables include run IDs, event IDs, timestamps, source
names, quality status, and failure messages where applicable.
