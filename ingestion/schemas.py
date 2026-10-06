"""Pydantic schemas for CityBikes API data."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Location(BaseModel):
    """Location schema for network."""

    city: str
    country: str
    latitude: float
    longitude: float


class NetworkSummary(BaseModel):
    """Network summary from /v2/networks endpoint."""

    id: str
    name: str
    href: str
    company: str | list[str]
    location: Location
    gbfs_href: str | None = None
    ebikes: bool | None = None


class NetworkListResponse(BaseModel):
    """Response from /v2/networks endpoint."""

    networks: list[NetworkSummary]


class StationExtra(BaseModel):
    """Extra fields for station."""

    uid: str | None = None
    renting: (int | str) | None = None
    returning: (int | str) | None = None
    last_updated: (int | str) | None = None
    has_ebikes: bool | None = None
    ebikes: (int | str) | None = None
    payment: list[str] | None = None
    payment_terminal: bool | None = Field(None, alias="payment-terminal")
    slots: (int | str) | None = None
    rental_uris: dict | None = None

    model_config = ConfigDict(populate_by_name=True)


class Station(BaseModel):
    """Station schema from network details endpoint."""

    id: str
    name: str
    latitude: float
    longitude: float
    timestamp: str  # UTC timestamp string
    free_bikes: int
    empty_slots: int | None = 0
    extra: StationExtra | None = None

    @field_validator('empty_slots', mode='before')
    @classmethod
    def convert_none_to_zero(cls, v):
        """Convert None to 0 for empty_slots."""
        if v is None:
            return 0
        return v


class Vehicle(BaseModel):
    """Vehicle schema (for roaming vehicles)."""

    id: str
    latitude: float
    longitude: float
    timestamp: str
    extra: dict | None = None
    kind: str | None = None  # "bike", "ebike", "scooter"


class NetworkDetails(BaseModel):
    """Network details from /v2/networks/{network_id} endpoint."""

    id: str
    name: str
    href: str
    company: str | list[str]
    location: Location
    gbfs_href: str | None = None
    ebikes: bool | None = None
    stations: list[Station]
    vehicles: list[Vehicle] | None = None


class NormalizedStation(BaseModel):
    """Normalized station record for storage."""

    station_id: str = Field(alias="id")
    name: str
    latitude: float
    longitude: float
    free_bikes: int
    empty_slots: int
    slots: int | None = None  # Total capacity from extra.slots, or free_bikes + empty_slots
    timestamp: str  # Original station timestamp from API
    ingestion_timestamp: datetime  # When we ingested the data
    city: str  # City name from network location
    extra: dict[str, Any] | None = None  # Raw extra field as JSON

    model_config = ConfigDict(populate_by_name=True, extra="ignore")
