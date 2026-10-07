## Goal Description
The goal of this project is to modernize and scale an existing Python-based ingestion script that extracts bike-share data from the CityBikes API. 

The new architecture implements industry-standard production practices:
1. **Orchestration**: Schedule ingestion every 30 minutes using Apache Airflow.
2. **Operational Storage (ODS)**: Store extracted, validated data into a single PostgreSQL table (`stations`), optimized with indexes on `(city, timestamp)` for high performance querying across cities.
3. **Change Data Capture (CDC)**: Implement Debezium and Kafka reading from the PostgreSQL WAL (`wal_level=logical`) to stream real-time data changes into a single Kafka topic.
4. **Data Lifecycle (Streaming to Data Lake)**: Continuously stream CDC events to MinIO (S3) in Parquet format using the Confluent S3 Sink, partitioned by date (`YYYY/MM/dd`). This allows historical analytics without database bloat.
5. **Robustness**: Strict Pydantic validation, exponential backoff/retries, idempotency to avoid duplicates, Flyway for database migrations.

## Implemented Changes

### Infrastructure (`docker-compose.yml`)
Expanded the Postgres setup to include the full data stack:
- `flyway`: Runs SQL migrations against Postgres.
- `minio` & `minio-setup`: Local S3 equivalent for the data lake and an init container to create the `citybikes-archive` bucket.
- `airflow-*`: Webserver, scheduler, and init for orchestration.
- `zookeeper` & `kafka`: Event bus for CDC.
- `kafka-connect`: Custom image loaded with Debezium and Confluent S3 plugins.

### Python Pipeline Core (`ingestion/` and `scripts/`)
- `PostgresStorage`: Implements the storage interface utilizing `psycopg2` `execute_values` for bulk inserts with `ON CONFLICT DO NOTHING` idempotency.
- `run_ingestion.py`: Hooks into the pipeline to execute the extraction and Postgres loading.

### Airflow Orchestration (`dags/`)
- `citybikes_ingestion_dag.py`: Airflow DAG scheduled at `*/30 * * * *`, utilizing the PythonOperator to run the ingestion task.

### Database Migrations (`db/migrations/`)
- `V1__initial_setup.sql`: Base schema definition containing the `stations` table, roles, and indices.

### CDC and S3 Integration (`cdc/`)
- `register-postgres.json`: Configures the Debezium source connector, employing the `ExtractNewRecordState` SMT to flatten the event payload.
- `register-s3-sink.json`: Configures the S3 sink connector to output Parquet files partitioned by time (`YYYY/MM/dd`) using a time-based partitioner.

## Verification Plan
### Manual Verification
1. Run `docker compose up -d` and ensure all containers become healthy.
2. Register the Kafka connectors using the `curl` commands from `docs/commands.md`.
3. Trigger the `ingestion_dag` manually from the Airflow UI (`localhost:8080`).
4. Query Postgres to verify the `stations` table is populated.
5. Trigger the DAG again and verify row counts do not increase (Idempotency).
6. Check the Kafka UI or use `kafka-console-consumer.sh` to verify Debezium is streaming CDC events to the topic.
7. Open the MinIO UI (`localhost:9001`) and verify the presence of Parquet files inside `citybikes-archive` structured by date folders.

## Data Warehousing with dbt & DuckDB
To enable high-performance analytics, we will introduce a modern data stack analytics layer:
1. **Compute & Storage Engine**: DuckDB will serve as the local analytical database.
2. **Transformations (ELT)**: `dbt` (Data Build Tool) will orchestrate the data models.
3. **Incremental Loading**: A staging layer (`stg_stations`) will read Parquet files from MinIO via DuckDB's `httpfs` extension and incrementally append new data into a local DuckDB file (`warehouse.duckdb`). This solves the "small files" problem from Kafka Connect and insulates analytical queries from network latency.

### Planned dbt Structure (`dbt_analytics/`)
- `profiles.yml`: Configures the `dbt-duckdb` adapter with S3 credentials pointing to local MinIO.
- `models/staging/sources.yml`: Defines the external MinIO Parquet path.
- `models/staging/stg_stations.sql`: The incremental base model capturing new records.

### MotherDuck Cloud Integration (Hybrid Push)
To serve BI dashboards in the cloud without exposing the local MinIO instance to the internet, we implement a Hybrid Push pattern:
1. `dbt` builds the analytics layer entirely locally inside `warehouse.duckdb`.
2. A post-ETL Python script (`push_to_motherduck.py`) connects to the local DuckDB instance, attaches the MotherDuck cloud database (`md:citybikes`), and issues `CREATE OR REPLACE TABLE cloud.table AS SELECT * FROM local.table` commands to sync the final tables to the cloud.
