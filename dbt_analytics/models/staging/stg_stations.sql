{{ config(
    materialized='incremental',
    unique_key=['station_id', 'timestamp']
) }}

WITH raw AS (
    SELECT * 
    FROM {{ source('datalake', 'raw_stations') }}
)

SELECT
    station_id,
    name,
    city,
    latitude,
    longitude,
    free_bikes,
    empty_slots,
    slots,
    CAST(timestamp AS TIMESTAMPTZ) AS timestamp,
    CAST(ingestion_timestamp AS TIMESTAMPTZ) AS ingestion_timestamp
FROM raw

{% if is_incremental() %}
    -- Only load new rows based on the max timestamp currently in DuckDB
    WHERE CAST(timestamp AS TIMESTAMPTZ) > (SELECT max(timestamp) FROM {{ this }})
{% endif %}
