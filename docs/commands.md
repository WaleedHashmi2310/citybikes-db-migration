# Useful Commands

## Docker & Infrastructure

**Start the stack:**
```bash
docker compose up -d
```

**View logs of a specific service:**
```bash
docker compose logs -f postgres
```

**Restart a service:**
```bash
docker compose restart airflow-scheduler
```

**Tear down everything (CAUTION: removes volumes and wipes all database/S3 data if you add `-v`):**
```bash
docker compose down -v
```

## PostgreSQL / Flyway

**Connect to the database via terminal:**
```bash
docker exec -it citybikes_postgres psql -U citybikes_admin -d citybikes
```

**Run Flyway migrations manually (if not auto-run on boot):**
```bash
docker compose run --rm flyway migrate
```

## Airflow

**Access the Airflow web UI:**
- URL: `http://localhost:8080`
- User/Pass: `airflow` / `airflow`

**Trigger a DAG manually via CLI:**
```bash
docker exec -it airflow-webserver airflow dags trigger citybikes_ingestion_dag
```

## MinIO (S3)

**Access the MinIO Web Console:**
- URL: `http://localhost:9001`
- User/Pass: `minioadmin` / `minioadmin`

## Kafka & Debezium

**List Kafka Topics:**
```bash
docker exec -it kafka /opt/bitnami/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

**Consume messages from a CDC topic:**
```bash
docker exec -it kafka /opt/bitnami/kafka/bin/kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic pg.citybikes.stations \
    --from-beginning
```

**Register Debezium Source Connector:**
```bash
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" \
localhost:8083/connectors/ -d @cdc/register-postgres.json
```

**Register Confluent S3 Sink Connector:**
```bash
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" \
localhost:8083/connectors/ -d @cdc/register-s3-sink.json
```

**Check Connectors Status:**
```bash
curl -s http://localhost:8083/connectors/ | jq
```
