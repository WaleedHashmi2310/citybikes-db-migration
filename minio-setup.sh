#!/bin/sh
apk add --no-cache curl aws-cli
# Wait for MinIO to be ready
echo "Waiting for MinIO..."
until curl -s http://minio:9000/minio/health/live; do
  sleep 1
done
echo "MinIO is ready. Creating bucket..."

export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin
export AWS_DEFAULT_REGION=us-east-1

# Create bucket using AWS CLI targeting MinIO
aws --endpoint-url http://minio:9000 s3 mb s3://citybikes-archive || echo "Bucket already exists"
