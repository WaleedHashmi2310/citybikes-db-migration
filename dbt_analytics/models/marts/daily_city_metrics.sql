{{ config(
    materialized='table'
) }}

WITH stations AS (
    SELECT * FROM {{ ref('stg_stations') }}
)

SELECT
    city,
    date_trunc('day', timestamp) AS date,
    count(DISTINCT station_id) AS total_stations,
    avg(free_bikes) AS avg_free_bikes,
    avg(empty_slots) AS avg_empty_slots,
    max(free_bikes) AS max_free_bikes
FROM stations
GROUP BY 1, 2
ORDER BY date DESC, city ASC
