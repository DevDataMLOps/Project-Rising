CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS pipeline_runs (
    pipeline_run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_name VARCHAR(150) NOT NULL,
    source_name VARCHAR(150),
    file_name TEXT,
    record_count_in INTEGER NOT NULL DEFAULT 0,
    record_count_valid INTEGER NOT NULL DEFAULT 0,
    record_count_rejected INTEGER NOT NULL DEFAULT 0,
    record_count_dlq INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    checksum VARCHAR(128)
);

CREATE TABLE IF NOT EXISTS processed_files (
    processed_file_id BIGSERIAL PRIMARY KEY,
    file_name TEXT NOT NULL,
    checksum VARCHAR(128) NOT NULL,
    ingestion_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    pipeline_run_id UUID REFERENCES pipeline_runs(pipeline_run_id),
    UNIQUE (file_name, checksum)
);

CREATE TABLE IF NOT EXISTS processed_events (
    event_fingerprint CHAR(64) PRIMARY KEY,
    event_id VARCHAR(100),
    source_topic VARCHAR(150),
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dead_letter_events (
    dead_letter_event_id BIGSERIAL PRIMARY KEY,
    original_payload JSONB NOT NULL,
    error_type VARCHAR(150) NOT NULL,
    error_message TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    failed_at TIMESTAMPTZ NOT NULL,
    source_topic VARCHAR(150) NOT NULL,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_metrics (
    metric_id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(150) NOT NULL,
    metric_name VARCHAR(150) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_unit VARCHAR(50),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
