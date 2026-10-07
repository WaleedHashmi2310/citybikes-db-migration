import duckdb
import os
import sys
from dotenv import load_dotenv

def main():
    # Load .env from the parent directory
    load_dotenv(dotenv_path="../.env")
    
    token = os.getenv("MOTHERDUCK_TOKEN")
    if not token or token == "your_token_here":
        print("Error: MOTHERDUCK_TOKEN environment variable is not set properly in .env")
        sys.exit(1)

    print("Connecting to local warehouse...")
    # Connect to local database
    con = duckdb.connect("warehouse.duckdb")

    print("Attaching MotherDuck cloud database...")
    # Load the MotherDuck extension and attach
    con.execute("INSTALL md;")
    con.execute("LOAD md;")
    
    # Attach MotherDuck (this attaches all your cloud databases)
    con.execute("ATTACH 'md:';")

    # Ensure the citybikes database and public schema exist
    con.execute("CREATE DATABASE IF NOT EXISTS citybikes;")
    con.execute("CREATE SCHEMA IF NOT EXISTS citybikes.public;")

    print("Syncing mart tables to the cloud...")
    
    # Get all tables from the main schema (our local dbt models)
    # Exclude stg_stations to save bandwidth (it's massive)
    tables_df = con.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog = 'warehouse' AND table_schema = 'main' AND table_name != 'stg_stations'").df()
    tables = tables_df['table_name'].tolist()
    
    for table in tables:
        print(f" - Syncing {table} to public schema...")
        # Drop old view if it exists so we can create a table (ignore error if it's already a table)
        try:
            con.execute(f"DROP VIEW IF EXISTS citybikes.public.{table};")
        except Exception:
            pass
        con.execute(f"CREATE OR REPLACE TABLE citybikes.public.{table} AS SELECT * FROM {table};")
        # Clean up any lingering tables in main
        try:
            con.execute(f"DROP TABLE IF EXISTS citybikes.main.{table};")
        except Exception:
            pass

    print("\n✅ Successfully pushed all marts to MotherDuck's public schema!")
    print("You can now query your data in Looker Studio or connect your BI tool to md:citybikes")

if __name__ == "__main__":
    main()
