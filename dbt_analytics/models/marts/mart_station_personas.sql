{{ config(materialized='table') }}
WITH velocity AS (
    SELECT * FROM {{ ref('mart_estimated_station_velocity') }}
),
day_types AS (
    SELECT 
        station_id, name, city,
        CASE WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN 'Weekend' ELSE 'Weekday' END as day_type,
        SUM(total_velocity) as total_activity,
        COUNT(DISTINCT date) as days_counted
    FROM velocity
    GROUP BY 1, 2, 3, 4
),
averages AS (
    SELECT 
        station_id, name, city,
        MAX(CASE WHEN day_type = 'Weekday' THEN total_activity / NULLIF(days_counted, 0) ELSE 0 END) as avg_weekday_activity,
        MAX(CASE WHEN day_type = 'Weekend' THEN total_activity / NULLIF(days_counted, 0) ELSE 0 END) as avg_weekend_activity
    FROM day_types
    GROUP BY 1, 2, 3
)
SELECT 
    *,
    CASE 
        WHEN avg_weekend_activity > avg_weekday_activity * 1.5 THEN 'Tourist/Recreational'
        WHEN avg_weekday_activity > avg_weekend_activity * 1.5 THEN 'Commuter'
        ELSE 'Balanced'
    END as persona
FROM averages
