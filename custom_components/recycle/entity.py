"""Recycle! integration base entity."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .api import ApiClient, ApiAddress
from .api_model import Collection, Fraction, Communication
from .const import (
    COLLECTIONS_TIMEFRAME,
    DOMAIN,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class RecycleDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Class to manage fetching Recycle! api data."""

    def __init__(
            self,
            hass: HomeAssistant,
            api_client: ApiClient,
            api_address: ApiAddress,
            fractions_ignore: list[str] = None,
            collections_timeframe: int = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api_client = api_client
        self.api_address = api_address
        self.fractions_ignore = fractions_ignore or []
        self.collections_timeframe = collections_timeframe or COLLECTIONS_TIMEFRAME

        self.collections: list[Collection] = []
        self.fractions: list[Fraction] = []

    async def _async_update_data(self) -> None:
        """Update data from Recycle! api."""
        _LOGGER.debug('Fetching recycle information for: {}'.format(self.api_address))

        timeframe = timedelta(days=self.collections_timeframe)

        api_collections = await self.api_client.get_collections(self.api_address, time_delta=timeframe)
        self.collections = [collection for collection in api_collections if collection.fraction.id not in self.fractions_ignore]

        api_fractions = await self.api_client.get_fractions(self.api_address)
        self.fractions = [fraction for fraction in api_fractions if fraction.id not in self.fractions_ignore]

        return None


class RecycleCoordinatorEntity(CoordinatorEntity):
    coordinator: RecycleDataUpdateCoordinator

    def __init__(self, coordinator: RecycleDataUpdateCoordinator, name_suffix: str, id_suffix: str = None, entity_id_format: str = None):
        super().__init__(coordinator)
        self._attr_name = '{} {}'.format(coordinator.config_entry.title, name_suffix)
        if coordinator.config_entry.unique_id:
            self._attr_unique_id = '{}-{}'.format(coordinator.config_entry.unique_id, id_suffix or name_suffix.lower())
        if entity_id_format:
            entity_name = '{}_{}'.format(coordinator.config_entry.title, id_suffix or name_suffix)
            self.entity_id = generate_entity_id(entity_id_format, name=entity_name, hass=self.coordinator.hass)
