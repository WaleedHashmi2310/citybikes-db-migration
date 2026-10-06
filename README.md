# CityBikes Database Migration & CDC Pipeline

🚧 **Status: Work In Progress** 🚧

## Overview
This project extracts real-time bike-sharing data from the [CityBikes API](http://api.citybik.es/v2/), normalizes it via `pydantic`, and stores it into a robust PostgreSQL operational database. 

## Tech Stack
* **Extraction:** Python 3.12 (Requests, Pydantic)
* **Orchestration:** Apache Airflow
* **Operational Database:** PostgreSQL 16
* **Database Migrations:** Flyway
* **Archival Storage:** MinIO / AWS S3 (via Parquet) *[In Progress]*
* **Real-time CDC:** Debezium & Kafka *[Planned]*
* **Containerization:** Docker Compose

## Quick Start
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Build and start the infrastructure:
   ```bash
   docker compose up -d --build
   ```
3. Access Airflow at `http://localhost:8080` to toggle the ingestion DAG.

*Detailed documentation can be found in the `docs/` folder.*
