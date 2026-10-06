# Pipeline Progress Tracker

## Phase 1: Infrastructure & DB Migrations [x]
- [x] Configure base PostgreSQL Docker container (`wal_level=logical`).
- [x] Set up Flyway in Docker Compose for database migrations.
- [x] Create initial Flyway SQL scripts (schemas, roles, base table templates).

## Phase 2: Python Ingestion Modifications [x]
- [x] Create `PostgresStorage` class implementing `StorageInterface`.
- [x] Implement robust bulk insert logic into the single `stations` table using `psycopg2` `execute_values`.
- [x] Add idempotency (handling duplicates based on `station_id` and `timestamp`).
- [x] Modify `run_ingestion.py` to only use PostgreSQL.

## Phase 3: Orchestration (Apache Airflow) [x]
- [x] Add Airflow services to `docker-compose.yml`.
- [x] Create `dags/` folder.
- [x] Write `citybikes_ingestion_dag.py` (schedule: `*/30 * * * *`).
- [x] Configure Airflow Postgres connection and environment variables.

## Phase 4: Bulk Load (Postgres -> S3) [x]
- [x] Write an Airflow task (`PythonOperator`) to extract data older than 3 days.
- [x] Write logic to convert extracted data to Parquet.
- [x] Upload to S3/MinIO.
- [x] Delete successfully uploaded records from Postgres.
- [x] Test the daily purge DAG (pending execution).

## Phase 5: Change Data Capture (CDC) [ ]
- [ ] Add Kafka, Zookeeper, and Kafka Connect (Debezium) to `docker-compose.yml`.
- [ ] Register Postgres Debezium connector via REST API.
- [ ] Verify Kafka topics are populated upon new inserts into Postgres.

## Phase 6: Observability [ ]
- [ ] Implement standard Python JSON logging in the ingestion scripts.
- [ ] Add basic Prometheus metrics to Airflow/Kafka.
