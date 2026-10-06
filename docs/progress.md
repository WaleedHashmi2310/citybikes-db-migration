# Pipeline Progress Tracker

## Phase 1: Infrastructure & DB Migrations [x]
- [x] Configure base PostgreSQL Docker container (`wal_level=logical`).
- [x] Set up Flyway in Docker Compose for database migrations.
- [x] Create initial Flyway SQL scripts (schemas, roles, base table templates).

## Phase 2: Python Ingestion Modifications [x]
- [x] Create `PostgresStorage` class implementing `StorageInterface`.
- [x] Implement robust bulk insert logic into the single `stations` table using `psycopg2` `execute_values`.
- [x] Add idempotency (handling ON CONFLICT collisions based on the fixed primary key: `city, station_id, timestamp`).
- [x] Modify `run_ingestion.py` to only use PostgreSQL.

## Phase 3: Orchestration (Apache Airflow) [x]
- [x] Add Airflow services to `docker-compose.yml`.
- [x] Create `dags/` folder.
- [x] Write `citybikes_ingestion_dag.py` (schedule: `*/30 * * * *`).
- [x] Configure Airflow Postgres connection and environment variables.

## Phase 4: Change Data Capture (Debezium CDC) [x]
- [x] Add Kafka, Zookeeper, and Kafka Connect to `docker-compose.yml`.
- [x] Build custom Kafka Connect Docker image containing both Debezium Postgres and Confluent S3 Sink plugins.
- [x] Register Postgres Debezium connector via REST API (`cdc/register-postgres.json`).
- [x] Apply `ExtractNewRecordState` SMT to strip Debezium envelope for a clean schema.
- [x] Verify Kafka topics (`pg.citybikes.stations`) are populated upon new inserts into Postgres.

## Phase 5: S3 Archive Dump (Kafka -> MinIO) [x]
- [x] Set up MinIO (`elestio/minio`) and AWS CLI setup container to automate `citybikes-archive` bucket creation.
- [x] Configure Confluent S3 Sink connector (`cdc/register-s3-sink.json`).
- [x] Dump records directly to MinIO in Parquet format.
- [x] Apply intuitive time-based partitioning scheme (`YYYY/MM/dd`).

## Phase 6: Observability [ ]
- [ ] Implement standard Python JSON logging in the ingestion scripts.
- [ ] Add basic Prometheus metrics to Airflow/Kafka.
