{{ config(materialized='table') }}
WITH morning_velocity AS (
    SELECT 
        station_id, name, city, latitude, longitude,
        LAG(free_bikes) OVER (PARTITION BY station_id, date_trunc('day', timestamp) ORDER BY timestamp) as prev_free_bikes,
        free_bikes
    FROM {{ ref('stg_stations') }}
    WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 7 AND 9
),
morning_diff AS (
    SELECT 
        station_id, name, city, latitude, longitude,
        SUM(CASE WHEN prev_free_bikes > free_bikes THEN prev_free_bikes - free_bikes ELSE 0 END) as total_morning_rentals,
        SUM(CASE WHEN free_bikes > prev_free_bikes THEN free_bikes - prev_free_bikes ELSE 0 END) as total_morning_returns
    FROM morning_velocity
    WHERE prev_free_bikes IS NOT NULL
    GROUP BY 1, 2, 3, 4, 5
)
SELECT 
    *,
    CASE 
        WHEN total_morning_rentals > total_morning_returns * 1.5 THEN 'Morning Source (Residential)'
        WHEN total_morning_returns > total_morning_rentals * 1.5 THEN 'Morning Sink (Commercial)'
        ELSE 'Neutral'
    END as flow_category
FROM morning_diff
