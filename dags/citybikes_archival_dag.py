import logging
import os
from datetime import datetime, timedelta

import boto3
import pandas as pd
import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator
from botocore.client import Config

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'citybikes',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Configuration for S3 (defaults point to local MinIO)
S3_BUCKET = os.getenv("S3_ARCHIVE_BUCKET", "citybikes-archive")
S3_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin123")
DB_URL = os.getenv("DATABASE_URL")
DAYS_TO_RETAIN = 3

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version='s3v4')
    )

def create_bucket_if_missing():
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except Exception as e:
        logger.info(f"Bucket {S3_BUCKET} does not exist, creating...")
        s3.create_bucket(Bucket=S3_BUCKET)

def archive_old_data(**kwargs):
    if not DB_URL:
        raise ValueError("DATABASE_URL must be set in Airflow environment")
    
    # 1. Connect to Postgres
    conn = psycopg2.connect(DB_URL)
    
    # Target date: older than DAYS_TO_RETAIN days
    target_date = datetime.now() - timedelta(days=DAYS_TO_RETAIN)
    
    try:
        with conn.cursor() as cur:
            # 2. Extract Data
            query = "SELECT * FROM citybikes.stations WHERE timestamp < %s"
            cur.execute(query, (target_date,))
            rows = cur.fetchall()
            
            if not rows:
                logger.info(f"No data older than {DAYS_TO_RETAIN} days found. Nothing to archive.")
                return
            
            col_names = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=col_names)
            logger.info(f"Extracted {len(df)} rows to archive.")
            
            # 3. Convert to Parquet locally (tmp inside container)
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_file = f"/tmp/stations_archive_{date_str}.parquet"
            
            # Handle timezone naive/aware conversions for pyarrow
            for col in df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
                df[col] = df[col].dt.tz_localize(None)
                
            df.to_parquet(local_file, engine='pyarrow', index=False)
            
            # 4. Upload to S3/MinIO
            create_bucket_if_missing()
            s3 = get_s3_client()
            s3_key = f"archive/{datetime.now().strftime('%Y/%m/%d')}/stations_{date_str}.parquet"
            s3.upload_file(local_file, S3_BUCKET, s3_key)
            logger.info(f"Successfully uploaded to s3://{S3_BUCKET}/{s3_key}")
            
            # 5. Delete from Postgres
            delete_query = "DELETE FROM citybikes.stations WHERE timestamp < %s"
            cur.execute(delete_query, (target_date,))
            conn.commit()
            deleted_rows = cur.rowcount
            logger.info(f"Deleted {deleted_rows} old records from Postgres.")
            
            # Clean up local file
            if os.path.exists(local_file):
                os.remove(local_file)
                
    except Exception as e:
        conn.rollback()
        logger.error(f"Archival failed: {e}")
        raise
    finally:
        conn.close()

with DAG(
    'citybikes_archival_dag',
    default_args=default_args,
    description='Export >3 days old data to S3 Parquet and delete from DB',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['archival', 's3', 'postgres'],
) as dag:

    run_archival = PythonOperator(
        task_id='export_and_purge_old_data',
        python_callable=archive_old_data,
        provide_context=True,
    )

    run_archival
