from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .const import DOMAIN, LOGGER


class RecycleEntity(CoordinatorEntity, Entity):
    pass


class RecycleDataUpdateCoordinator(DataUpdateCoordinator[RecycleData]):
    """Class to manage fetching Recycle! api data."""

    def __init__(
            self,
            hass: HomeAssistant,
            session: ClientSession,
            update_interval: timedelta,
            address_info: None,  # @TODO address model
            calendar_interval: timedelta = timedelta(days=14),
    ) -> None:
        super().__init__(hass, LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self) -> RecycleData:
        """Update data via library."""
        # @TODO call recycle api
        return RecycleData()
