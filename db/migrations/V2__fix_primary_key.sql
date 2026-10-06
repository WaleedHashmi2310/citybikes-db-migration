-- Drop the old primary key constraint
ALTER TABLE citybikes.stations DROP CONSTRAINT stations_pkey;

-- Add a new composite primary key that includes city to prevent cross-city station_id collisions
ALTER TABLE citybikes.stations ADD PRIMARY KEY (city, station_id, timestamp);
