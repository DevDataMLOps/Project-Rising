CREATE TABLE IF NOT EXISTS fact_health_observation (
    health_observation_key BIGSERIAL PRIMARY KEY,
    country_key INTEGER NOT NULL REFERENCES dim_country(country_key),
    indicator_key INTEGER NOT NULL REFERENCES dim_indicator(indicator_key),
    date_key INTEGER REFERENCES dim_date(date_key),
    source_key INTEGER REFERENCES dim_source(source_key),
    quality_status_key INTEGER REFERENCES dim_quality_status(quality_status_key),
    year INTEGER NOT NULL,
    sub_indicator TEXT,
    sex VARCHAR(20),
    unit TEXT,
    value NUMERIC NOT NULL,
    ingestion_batch_id UUID,
    event_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_health_observation_natural_key
ON fact_health_observation (
    country_key,
    indicator_key,
    year,
    COALESCE(sub_indicator, ''),
    COALESCE(sex, '')
);

CREATE TABLE IF NOT EXISTS fact_weather_observation (
    weather_observation_key BIGSERIAL PRIMARY KEY,
    country_key INTEGER NOT NULL REFERENCES dim_country(country_key),
    station_key INTEGER REFERENCES dim_station(station_key),
    date_key INTEGER REFERENCES dim_date(date_key),
    source_key INTEGER REFERENCES dim_source(source_key),
    quality_status_key INTEGER REFERENCES dim_quality_status(quality_status_key),
    event_id VARCHAR(100) NOT NULL UNIQUE,
    observed_at TIMESTAMPTZ NOT NULL,
    temperature_c NUMERIC NOT NULL,
    humidity_pct NUMERIC NOT NULL,
    rainfall_mm NUMERIC NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
