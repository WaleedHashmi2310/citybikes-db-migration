from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'citybikes',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'citybikes_ingestion_dag',
    default_args=default_args,
    description='Extract CityBikes data and load into PostgreSQL',
    schedule_interval='*/30 * * * *', # Every 30 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ingestion', 'postgres'],
) as dag:

    run_ingestion_script = BashOperator(
        task_id='run_python_ingestion',
        # The scripts directory is mounted at /opt/airflow/scripts
        # The environment variables (DATABASE_URL) are injected natively via docker-compose
        bash_command='python /opt/airflow/scripts/run_ingestion.py',
    )

    run_ingestion_script

