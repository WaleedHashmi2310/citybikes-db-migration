CREATE SCHEMA IF NOT EXISTS citybikes;

CREATE TABLE IF NOT EXISTS citybikes.stations (
    station_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    free_bikes INTEGER,
    empty_slots INTEGER,
    slots INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ingestion_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    city VARCHAR(100) NOT NULL,
    extra JSONB,
    PRIMARY KEY (station_id, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_stations_city_timestamp ON citybikes.stations(city, timestamp);
