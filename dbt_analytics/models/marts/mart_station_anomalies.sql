{{ config(materialized='table') }}
WITH historical_stats AS (
    SELECT 
        station_id,
        EXTRACT(HOUR FROM timestamp) as hour_of_day,
        AVG(free_bikes) as avg_bikes,
        STDDEV(free_bikes) as stddev_bikes
    FROM {{ ref('stg_stations') }}
    WHERE timestamp < current_date
    GROUP BY 1, 2
),
latest_status AS (
    SELECT * FROM {{ ref('mart_station_health_latest') }}
)
SELECT 
    l.station_id, l.name, l.city, l.free_bikes as current_bikes, 
    h.avg_bikes as historical_avg_for_hour,
    h.stddev_bikes,
    CASE 
        WHEN h.stddev_bikes = 0 THEN 0
        ELSE ABS(l.free_bikes - h.avg_bikes) / h.stddev_bikes 
    END as z_score
FROM latest_status l
JOIN historical_stats h 
  ON l.station_id = h.station_id 
  AND EXTRACT(HOUR FROM l.last_updated) = h.hour_of_day
WHERE (CASE WHEN h.stddev_bikes = 0 THEN 0 ELSE ABS(l.free_bikes - h.avg_bikes) / h.stddev_bikes END) > 2.0
