{{ config(materialized='table') }}
WITH ranked_stations AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY station_id ORDER BY timestamp DESC) as rn
    FROM {{ ref('stg_stations') }}
)
SELECT 
    station_id, name, city, latitude, longitude,
    free_bikes, empty_slots, slots, timestamp as last_updated,
    CASE 
        WHEN free_bikes = 0 THEN 'Empty'
        WHEN empty_slots = 0 THEN 'Full'
        ELSE 'Healthy'
    END as status
FROM ranked_stations
WHERE rn = 1
