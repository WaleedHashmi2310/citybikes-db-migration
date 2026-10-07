{{ config(materialized='table') }}
WITH max_daily_stations AS (
    SELECT 
        city,
        station_id,
        date_trunc('day', timestamp) as date,
        MAX(slots) as max_slots
    FROM {{ ref('stg_stations') }}
    GROUP BY 1, 2, 3
)
SELECT 
    city,
    date,
    SUM(max_slots) as total_city_fleet_capacity,
    COUNT(DISTINCT station_id) as active_stations
FROM max_daily_stations
GROUP BY 1, 2
ORDER BY date DESC, city ASC
