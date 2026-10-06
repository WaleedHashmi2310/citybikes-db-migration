"""CityBikes API client with retry logic."""

import logging

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ingestion.schemas import NetworkDetails, NetworkListResponse

logger = logging.getLogger(__name__)


class CityBikesClient:
    """Client for CityBikes API v2."""

    BASE_URL = "https://api.citybik.es/v2"

    def __init__(self, base_url: str | None = None):
        """
        Initialize client.

        Args:
            base_url: Optional base URL override (defaults to https://api.citybik.es/v2)
        """
        self.base_url = base_url or self.BASE_URL
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "citybikes-pipeline/0.1.0",
                "Accept": "application/json",
            }
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _make_request(self, endpoint: str) -> requests.Response:
        """
        Make HTTP request with retry logic.

        Args:
            endpoint: API endpoint path (e.g., "/networks")

        Returns:
            Response object

        Raises:
            requests.exceptions.HTTPError: For 4xx/5xx responses
            requests.exceptions.RequestException: For other request errors
        """
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Making request to {url}")

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Check rate limit headers
            remaining = response.headers.get("x-ratelimit-remaining-hour")
            if remaining:
                logger.debug(f"Rate limit remaining: {remaining}")

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_networks(self) -> NetworkListResponse:
        """
        Get all available networks.

        Returns:
            NetworkListResponse with list of network summaries

        Raises:
            requests.exceptions.HTTPError: For API errors
            ValidationError: If response doesn't match schema
        """
        logger.info("Fetching all networks")
        response = self._make_request("/networks")
        data = response.json()
        return NetworkListResponse.model_validate(data)

    def get_network_details(self, network_id: str) -> NetworkDetails:
        """
        Get detailed information for a specific network including stations.

        Args:
            network_id: Network identifier (e.g., "callabike-frankfurt")

        Returns:
            NetworkDetails with stations and metadata

        Raises:
            requests.exceptions.HTTPError: For API errors (including 404)
            ValidationError: If response doesn't match schema
        """
        logger.info(f"Fetching network details for {network_id}")
        response = self._make_request(f"/networks/{network_id}")
        data = response.json()
        return NetworkDetails.model_validate(data["network"])

    def test_connection(self) -> bool:
        """
        Test API connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._make_request("/networks")
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Connection test failed: {e}")
            return False
