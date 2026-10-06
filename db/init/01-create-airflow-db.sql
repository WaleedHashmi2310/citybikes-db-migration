CREATE DATABASE airflow;
CREATE USER airflow WITH PASSWORD 'airflow';
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
\c airflow
GRANT ALL ON SCHEMA public TO airflow;
