{{ config(materialized='table') }}
SELECT 
    city,
    ROUND(latitude, 2) as grid_lat,
    ROUND(longitude, 2) as grid_lon,
    COUNT(DISTINCT station_id) as total_stations,
    SUM(free_bikes) as current_free_bikes,
    SUM(slots) as current_capacity,
    (SUM(free_bikes) * 100.0) / NULLIF(SUM(slots), 0) as percent_bikes_available
FROM {{ ref('mart_station_health_latest') }}
GROUP BY 1, 2, 3
