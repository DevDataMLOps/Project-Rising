CREATE TABLE IF NOT EXISTS dim_country (
    country_key SERIAL PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    region VARCHAR(50) NOT NULL DEFAULT 'ASEAN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_indicator (
    indicator_key SERIAL PRIMARY KEY,
    indicator_code VARCHAR(150) NOT NULL UNIQUE,
    indicator_label TEXT,
    description TEXT,
    unit TEXT,
    source_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    quarter INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_source (
    source_key SERIAL PRIMARY KEY,
    source_name VARCHAR(150) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL,
    source_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_station (
    station_key SERIAL PRIMARY KEY,
    station_id VARCHAR(50) NOT NULL UNIQUE,
    country_key INTEGER REFERENCES dim_country(country_key),
    station_name VARCHAR(150),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_quality_status (
    quality_status_key SERIAL PRIMARY KEY,
    quality_status VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);
