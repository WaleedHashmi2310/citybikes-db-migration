import logging
import json
from abc import ABC, abstractmethod
import psycopg2
from psycopg2.extras import execute_values
from ingestion.schemas import NormalizedStation

logger = logging.getLogger(__name__)

class StorageInterface(ABC):
    """Abstract interface for storing CityBikes data."""
    @abstractmethod
    def store_stations(self, stations: list[NormalizedStation]) -> str:
        pass

class PostgresStorage(StorageInterface):
    """PostgreSQL storage backend using psycopg2."""
    def __init__(self, dsn: str):
        self.dsn = dsn
        
    def store_stations(self, stations: list[NormalizedStation]) -> str:
        if not stations:
            return "No stations to store"
            
        logger.info(f"Connecting to PostgreSQL to store {len(stations)} stations")
        conn = psycopg2.connect(self.dsn)
        try:
            with conn.cursor() as cur:
                # Prepare data for execute_values
                records = []
                for s in stations:
                    records.append((
                        s.station_id,
                        s.name,
                        s.latitude,
                        s.longitude,
                        s.free_bikes,
                        s.empty_slots,
                        s.slots,
                        s.timestamp,
                        s.ingestion_timestamp,
                        s.city,
                        json.dumps(s.extra) if s.extra else None
                    ))
                
                # We target the single table as decided
                query = """
                    INSERT INTO citybikes.stations (
                        station_id, name, latitude, longitude, free_bikes, empty_slots, 
                        slots, timestamp, ingestion_timestamp, city, extra
                    ) VALUES %s
                    ON CONFLICT (city, station_id, timestamp) DO NOTHING;
                """
                
                execute_values(cur, query, records)
                conn.commit()
                # execute_values does not accurately return rowcount for ON CONFLICT DO NOTHING in some versions,
                # but we log success.
                logger.info(f"Successfully ran bulk insert for {len(records)} records (duplicates ignored via ON CONFLICT)")
                
                # Return a safe summary of the DB host
                db_host = self.dsn.split('@')[-1].split('/')[0] if '@' in self.dsn else "PostgreSQL Database"
                return f"PostgreSQL: {db_host}"
        except Exception as e:
            conn.rollback()
            logger.error(f"Database insertion failed: {e}")
            raise
        finally:
            conn.close()
