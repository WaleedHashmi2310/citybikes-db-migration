#!/usr/bin/env python3
"""
CityBikes Pipeline Ingestion Script

Run data ingestion from CityBikes API directly to PostgreSQL.

Usage:
    python scripts/run_ingestion.py [--networks network1,network2] [--verbose]

Environment variables (override via .env):
    DATABASE_URL: Postgres connection string
    CITYBIKES_NETWORKS: comma-separated network IDs (default: German cities)
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path to import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.client import CityBikesClient
from ingestion.extractor import CityBikesExtractor
from ingestion.loader import DataLoader
from ingestion.storage import PostgresStorage

# Default network IDs (German cities from extractor - high volume networks)
DEFAULT_NETWORKS = [
    "callabike-frankfurt",
    "visa-frankfurt",
    "callabike-koln",
    "kvb-rad-koln",
    "nextbike-dusseldorf",
    "stadtrad-hamburg-db",
    "callabike-munchen",
    "stadtrad-stuttgart",
    "mobibike-dresden",
    "nextbike-leipzig",
    "callabike-berlin",
    "mvg-meinrad-nextbike-mainz",
]

def setup_logging(verbose: bool = False):
    """Configure logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Reduce noise from third-party libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def parse_networks(networks_str: str) -> list[str]:
    """Parse comma-separated network IDs string."""
    if not networks_str:
        return DEFAULT_NETWORKS
    return [n.strip() for n in networks_str.split(",") if n.strip()]

def main():
    parser = argparse.ArgumentParser(
        description="CityBikes API data ingestion pipeline to PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--networks",
        type=str,
        help="Comma-separated list of network IDs to extract (default: German cities)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Log startup information
    logger.info("Starting CityBikes ingestion pipeline to PostgreSQL")

    # Get Database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)

    # Parse networks
    networks = parse_networks(args.networks or os.getenv("CITYBIKES_NETWORKS", ""))
    logger.info(f"Target networks: {networks}")

    # Initialize Postgres Storage
    storage = PostgresStorage(dsn=db_url)

    # Override extractor's network list via subclass
    class CustomExtractor(CityBikesExtractor):
        GERMAN_NETWORK_IDS = networks

    # Initialize pipeline components
    try:
        client = CityBikesClient()
        extractor = CustomExtractor(client=client)
        loader = DataLoader(extractor=extractor, storage=storage)

        # Test API connection
        logger.info("Testing API connection...")
        if not client.test_connection():
            logger.error("API connection test failed")
            sys.exit(1)
        logger.info("API connection successful")

        # Run ingestion
        logger.info("Starting data extraction and storage...")
        stations, storage_path = loader.load_all_stations()

        if not stations:
            logger.warning("No stations were extracted")
            sys.exit(0)

        logger.info(f"Successfully extracted {len(stations)} stations")
        logger.info(f"Data stored at: {storage_path}")

        # Fail the Airflow task if there were partial extraction errors, 
        # but only AFTER we have successfully saved the good data.
        if getattr(extractor, 'failed_count', 0) > 0:
            raise RuntimeError(f"Ingestion completed with {extractor.failed_count} failed networks. Check logs for 404s or timeouts.")
        # Log any failed networks to a dedicated file so we can monitor them without failing the DAG
        failed_networks = getattr(extractor, 'failed_networks', [])
        if failed_networks:
            import json
            from datetime import datetime
            log_file = Path("/opt/airflow/logs/failed_networks.jsonl")
            # Fallback for local testing outside of docker
            if not log_file.parent.exists():
                log_file = project_root / "logs" / "failed_networks.jsonl"
                log_file.parent.mkdir(exist_ok=True)
                
            with open(log_file, "a") as f:
                for failure in failed_networks:
                    failure["timestamp"] = datetime.now().isoformat()
                    f.write(json.dumps(failure) + "\n")
            logger.warning(f"Logged {len(failed_networks)} failed networks to {log_file}")

    except KeyboardInterrupt:
        logger.warning("Ingestion interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=args.verbose)
        sys.exit(1)

if __name__ == "__main__":
    main()