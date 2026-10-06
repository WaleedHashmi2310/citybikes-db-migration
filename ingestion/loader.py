"""Data loader bridging extraction and storage."""

import logging

from ingestion.extractor import CityBikesExtractor
from ingestion.schemas import NormalizedStation
from ingestion.storage import StorageInterface

logger = logging.getLogger(__name__)


class DataLoader:
    """Load extracted data to storage backend.

    Bridges the ingestion extractor and storage interface with minimal logic.

    Args:
        extractor: CityBikesExtractor instance
        storage: StorageInterface implementation (Postgres)
    """

    def __init__(self, extractor: CityBikesExtractor, storage: StorageInterface):
        self.extractor = extractor
        self.storage = storage
        logger.debug("Initialized DataLoader")

    def load_all_stations(self) -> tuple[list[NormalizedStation], str]:
        """Extract all stations and store them.

        Returns:
            Tuple of (stations list, storage_path_or_uri)

        Raises:
            StorageError: If storage operation fails
            requests.exceptions.RequestException: If extraction fails
        """
        logger.info("Starting data extraction and storage")

        # Extract stations from all target German cities
        stations = self.extractor.extract_all_stations()
        logger.info(f"Extracted {len(stations)} stations from all networks")

        if not stations:
            logger.warning("No stations extracted, nothing to store")
            return [], ""

        # Store stations using configured storage backend
        storage_path = self.storage.store_stations(stations)
        logger.info(f"Stored stations to: {storage_path}")

        return stations, storage_path
