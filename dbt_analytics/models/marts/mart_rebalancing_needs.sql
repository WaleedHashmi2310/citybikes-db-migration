{{ config(materialized='table') }}
SELECT 
    station_id, name, city, latitude, longitude,
    COUNT(*) as total_snapshots,
    SUM(CASE WHEN free_bikes = 0 THEN 1 ELSE 0 END) as empty_snapshots,
    SUM(CASE WHEN empty_slots = 0 THEN 1 ELSE 0 END) as full_snapshots,
    (SUM(CASE WHEN free_bikes = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(*) as percent_empty,
    (SUM(CASE WHEN empty_slots = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(*) as percent_full
FROM {{ ref('stg_stations') }}
WHERE timestamp >= current_date - interval '7' day
GROUP BY 1, 2, 3, 4, 5
