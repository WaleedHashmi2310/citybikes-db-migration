# CityBikes Pipeline Architecture

This document describes the stack and roles of each component in the data pipeline, including decisions and tradeoffs made.

## Stack Overview

1. **Python 3.12+ (Extraction & Transformation)**
   - Extracts data from CityBikes API.
   - Uses `pydantic` for strict schema validation.
   - **Tradeoff**: Python is slower than Go or Rust, but provides an unmatched ecosystem for data engineering and API interaction.

2. **PostgreSQL (Operational Store / Sink)**
   - Target database for the initial extraction.
   - Stores all data in a **single table** (e.g., `stations`).
   - **Decision/Tradeoff**: We opted for a single table over one-table-per-city. This simplifies CDC (one Kafka topic instead of hundreds), avoids schema sprawl, and makes cross-city analytical queries trivial. Since only 3 days of data are retained, a single table with an index on `(city, timestamp)` is highly performant.

3. **Flyway (Database Migrations)**
   - Industry-standard version control for database schemas.
   - Handles the creation of roles, schemas, and initial tables.
   - **Tradeoff**: Requires writing raw SQL migrations instead of using Python ORMs like Alembic, but offers language-agnostic migration management.

4. **Apache Airflow (Orchestration)**
   - Schedules the ingestion script every 30 minutes.
   - Handles retries, idempotency, and alerts on failure.
   - Manages the bulk load step to S3.
   - **Tradeoff**: Airflow can be heavy to run locally, requiring its own database and scheduler components, but it is the industry standard for DAG execution and observability.

5. **Amazon S3 / Local MinIO (Cold Storage / Bulk Load)**
   - Stores batched, historical data older than 3 days to keep Postgres lightweight.
   - Data stored in Parquet format for analytical querying.
   - **Tradeoff**: Requires managing S3 buckets and IAM permissions, but dramatically lowers DB storage costs and enables data lake integrations.

6. **Debezium + Kafka (Change Data Capture - CDC)**
   - Reads the Postgres Write-Ahead Log (WAL) to detect every insert/update in real-time.
   - Pushes these events to Kafka topics.
   - **Tradeoff**: Introduces significant infrastructure complexity (Zookeeper, Kafka brokers, Kafka Connect workers) but ensures near real-time, zero-data-loss event streaming without overloading the database with polling queries.

7. **Observability (Logging & Monitoring)**
   - **Logging**: Python `logging` module outputting JSON to be ingested by Promtail/Loki or DataDog.
   - **Monitoring**: Prometheus (scraping Airflow/Kafka metrics) + Grafana.
