{{ config(materialized='table') }}
SELECT 
    city,
    EXTRACT(DOW FROM timestamp) as day_of_week,
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    AVG(free_bikes) as avg_free_bikes,
    AVG(empty_slots) as avg_empty_slots
FROM {{ ref('stg_stations') }}
GROUP BY 1, 2, 3
