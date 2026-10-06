# CityBikes Database Migration & CDC Pipeline

## Overview
This project extracts real-time bike-sharing data from the [CityBikes API](http://api.citybik.es/v2/), normalizes it via `pydantic`, and stores it into a robust PostgreSQL operational database. Changes are then captured via Debezium CDC and streamed to a MinIO S3 bucket in Parquet format using Kafka Connect.

## Tech Stack
* **Extraction:** Python 3.12 (Requests, Pydantic)
* **Orchestration:** Apache Airflow
* **Operational Database:** PostgreSQL 16
* **Database Migrations:** Flyway
* **Archival Storage:** MinIO (S3 compatible) via Kafka Connect Sink (Parquet format)
* **Real-time CDC:** Debezium & Kafka
* **Containerization:** Docker Compose

## End-to-End Execution
1. **Setup Environment:**
   ```bash
   cp .env.example .env
   ```
2. **Start Infrastructure:**
   ```bash
   docker compose up -d --build
   ```
3. **Accumulate Data (Airflow -> Postgres):**
   Access Airflow at `http://localhost:8080` (User/Pass: `airflow`) and trigger `citybikes_ingestion_dag`. Wait for the run to succeed.
4. **Enable CDC & Bulk Load (Postgres -> Kafka):**
   Register the Debezium connector. It will instantly snapshot existing data, then stream real-time WAL changes.
   ```bash
   curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" \
   localhost:8083/connectors/ -d @cdc/register-postgres.json
   ```
5. **Enable Data Lake Sink (Kafka -> MinIO):**
   Register the S3 Sink. It will consume the Kafka stream and write Parquet files to MinIO.
   ```bash
   curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" \
   localhost:8083/connectors/ -d @cdc/register-s3-sink.json
   ```
6. **Verify Archives:**
   Access MinIO at `http://localhost:9001` (User/Pass: `minioadmin`) to view the resulting Parquet files in the `citybikes-archive` bucket.

*Detailed documentation can be found in the `docs/` folder.*
