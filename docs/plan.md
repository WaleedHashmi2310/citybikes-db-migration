## Goal Description
The goal of this project is to modernize and scale an existing Python-based ingestion script that extracts bike-share data from the CityBikes API. 

The new architecture will implement industry-standard production practices:
1. **Orchestration**: Schedule ingestion every 30 minutes using Apache Airflow.
2. **Operational Storage (ODS)**: Store extracted, validated data into a single PostgreSQL table (`stations`), optimized with indexes on `(city, timestamp)` for high performance querying across cities.
3. **Data Lifecycle (Bulk Load)**: Accumulate data in Postgres for 3 days, then batch-export older data to MinIO (Local S3 equivalent) in Parquet format to prevent database bloat.
4. **Change Data Capture (CDC)**: Implement Debezium and Kafka reading from the PostgreSQL WAL (`wal_level=logical`) to stream real-time data changes into a single Kafka topic.
5. **Robustness**: Implement strict Pydantic validation, exponential backoff/retries, idempotency to avoid duplicates, Flyway for database migrations, and JSON logging for observability.

## Proposed Changes

### Infrastructure (`docker-compose.yml`)
Expand the current Postgres setup to include the full data stack.

#### [MODIFY] docker-compose.yml
```yaml
# Will append the following services:
# - flyway: To run SQL migrations against Postgres and establish the base schema.
# - minio: Local S3 equivalent for the bulk load target
# - airflow-webserver, airflow-scheduler, airflow-init: For orchestration
# - zookeeper & kafka: For the event bus
# - kafka-connect: For Debezium CDC
```

---

### Python Pipeline Core (`ingestion/` and `scripts/`)
Modify the pipeline to support the PostgreSQL target.

#### [NEW] ingestion/storage/postgres.py
```python
class PostgresStorage(StorageInterface):
    """PostgreSQL storage backend using psycopg2."""
    def __init__(self, dsn: str):
        # connection logic
        pass

    def store(self, data: list[NormalizedStation]) -> str:
        # 1. Insert data using execute_values into 'stations'
        # 2. Handle idempotency (ON CONFLICT (station_id, timestamp) DO NOTHING)
        pass
```

#### [MODIFY] scripts/run_ingestion.py
```python
# Add '--storage postgres' to argparse
# Instantiate PostgresStorage based on ENV vars
# Hook into the existing pipeline
```

---

### Airflow Orchestration (`dags/`)
Create the DAGs that will replace cron.

#### [NEW] dags/ingestion_dag.py
```python
# Airflow DAG scheduled at '*/30 * * * *'
# Uses DockerOperator or PythonOperator to run scripts/run_ingestion.py
```

#### [NEW] dags/archival_dag.py
```python
# Airflow DAG scheduled at '@daily'
# Runs a script to SELECT data older than 3 days, write to Parquet, upload to MinIO, and DELETE from Postgres.
```

---

### Database Migrations (`db/migrations/`)
Use Flyway to handle the core schema.

#### [NEW] db/migrations/V1__initial_setup.sql
```sql
CREATE SCHEMA IF NOT EXISTS citybikes;

CREATE TABLE citybikes.stations (
    station_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    free_bikes INTEGER,
    empty_slots INTEGER,
    slots INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ingestion_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    city VARCHAR(100) NOT NULL,
    extra JSONB,
    PRIMARY KEY (station_id, timestamp)
);

CREATE INDEX idx_stations_city_timestamp ON citybikes.stations(city, timestamp);
```

## Verification Plan
### Automated Tests
- Run `pytest` if test coverage exists for the storage interfaces.
- Use a mock DB to ensure the `PostgresStorage` correctly generates `INSERT ... ON CONFLICT` statements.

### Manual Verification
1. Run `docker compose up -d` and ensure all containers (Airflow, Kafka, Postgres, MinIO) become healthy.
2. Trigger the `ingestion_dag` manually from the Airflow UI.
3. Query Postgres to verify the `stations` table is populated.
4. Trigger the DAG again and verify row counts do not increase (Idempotency).
5. Check the Kafka UI or use `kafka-console-consumer.sh` to verify Debezium is streaming CDC events to the topic.
