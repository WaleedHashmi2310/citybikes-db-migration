{{ config(materialized='table') }}
WITH lag_data AS (
    SELECT 
        station_id, name, city, timestamp, free_bikes,
        LAG(free_bikes) OVER (PARTITION BY station_id ORDER BY timestamp) as prev_free_bikes
    FROM {{ ref('stg_stations') }}
),
diff_data AS (
    SELECT 
        *,
        -- If bikes decreased, it's a rental. If increased, it's a return.
        CASE WHEN prev_free_bikes > free_bikes THEN prev_free_bikes - free_bikes ELSE 0 END as rentals,
        CASE WHEN free_bikes > prev_free_bikes THEN free_bikes - prev_free_bikes ELSE 0 END as returns
    FROM lag_data
    WHERE prev_free_bikes IS NOT NULL
)
SELECT 
    station_id, name, city,
    date_trunc('day', timestamp) as date,
    SUM(rentals) as estimated_rentals,
    SUM(returns) as estimated_returns,
    SUM(rentals) + SUM(returns) as total_velocity
FROM diff_data
GROUP BY 1, 2, 3, 4
