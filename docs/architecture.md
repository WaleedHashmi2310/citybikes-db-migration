# CityBikes Pipeline Architecture

This document describes the stack and roles of each component in the data pipeline, including decisions and tradeoffs made.

## Stack Overview

1. **Python 3.12+ (Extraction & Transformation)**
   - Extracts data from CityBikes API.
   - Uses `pydantic` for strict schema validation.
   - **Tradeoff**: Python is slower than Go or Rust, but provides an unmatched ecosystem for data engineering and API interaction.

2. **PostgreSQL (Operational Store / Sink)**
   - Target database for the initial extraction.
   - Stores all data in a **single table** (`stations`).
   - **Decision/Tradeoff**: We opted for a single table over one-table-per-city. This simplifies CDC (one Kafka topic instead of hundreds), avoids schema sprawl, and makes cross-city analytical queries trivial.

3. **Flyway (Database Migrations)**
   - Industry-standard version control for database schemas.
   - Handles the creation of roles, schemas, and initial tables.
   - **Tradeoff**: Requires writing raw SQL migrations instead of using Python ORMs like Alembic, but offers language-agnostic migration management.

4. **Apache Airflow (Orchestration)**
   - Schedules the ingestion script every 30 minutes.
   - Handles retries, idempotency, and alerts on failure.
   - **Decision/Tradeoff**: Initially, we planned to use Airflow for S3 batch archival, but opted to use Kafka Connect for near real-time CDC archival instead. Airflow strictly manages the ingestion step. Airflow can be heavy to run locally, requiring its own database and scheduler components, but it is the industry standard for DAG execution.

5. **Debezium + Kafka (Change Data Capture - CDC)**
   - Reads the Postgres Write-Ahead Log (WAL) to detect every insert/update in real-time.
   - Pushes these events to Kafka topics.
   - Applies SMT (Single Message Transforms) like `ExtractNewRecordState` to strip the CDC envelope.
   - **Tradeoff**: Introduces significant infrastructure complexity (Zookeeper, Kafka brokers, Kafka Connect workers) but ensures near real-time, zero-data-loss event streaming without overloading the database with polling queries.

6. **Amazon S3 / Local MinIO (Cold Storage & Data Lake)**
   - Receives data streamed from Kafka via the Confluent S3 Sink connector.
   - Stores historical data in a time-partitioned folder structure (`YYYY/MM/dd`).
   - Data is serialized in **Parquet** format for columnar analytical querying.
   - **Tradeoff**: Moving from simple batch jobs to streaming sinks requires strict schema adherence (e.g., ensuring `value.converter.schemas.enable=true` is used correctly with SMTs), but provides continuous data delivery and eliminates big daily batch spikes.

7. **Observability (Logging)**
   - Python logging module outputs basic logs to standard out, captured by Docker Compose.

8. **DuckDB & dbt (Data Warehousing / Analytics)**
   - **DuckDB**: An in-process OLAP database used to query the Data Lake.
   - **dbt**: Data Build Tool orchestrates SQL transformations.
   - **Design/Tradeoff**: Instead of querying thousands of Parquet files directly over HTTP for every analytical question, dbt incrementally loads new data from MinIO into a local `.duckdb` file. This resolves the "small files" issue from the Kafka Sink, insulates the analytics engine from network latency, and leverages DuckDB's native fast storage format for heavy aggregations.
