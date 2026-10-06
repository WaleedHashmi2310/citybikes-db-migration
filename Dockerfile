FROM apache/airflow:2.9.2
RUN pip install --no-cache-dir pydantic psycopg2-binary requests pandas pyarrow boto3