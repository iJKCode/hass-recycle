"""Recycle! integration base entity."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .api import ApiClient, ApiAddress
from .api_model import Collection, Fraction, Communication
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, DEFAULT_COLLECTIONS_INTERVAL

_LOGGER = logging.getLogger(__name__)


class RecycleDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Recycle! api data."""

    def __init__(
            self,
            hass: HomeAssistant,
            api_client: ApiClient,
            api_address: ApiAddress,
            update_interval: timedelta = DEFAULT_SCAN_INTERVAL,
            collections_interval: timedelta = DEFAULT_COLLECTIONS_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)
        self.api_client = api_client
        self.api_address = api_address
        self.collections_interval = collections_interval

        self.collections: list[Collection] = []
        self.fractions: dict[str, Fraction] = {}
        self.communications: list[Communication] = []

    async def _async_update_data(self) -> None:
        """Update data from Recycle! api."""
        _LOGGER.info('Fetching recycle information for: {}'.format(self.config_entry.entry_id))

        self.collections = await self.api_client.get_collections(self.api_address, time_delta=self.collections_interval)

        return None


class RecycleCoordinatorEntity(CoordinatorEntity):
    coordinator: RecycleDataUpdateCoordinator

    def __init__(self, coordinator: RecycleDataUpdateCoordinator, suffix: str):
        super().__init__(coordinator)
        self._name = '{} {}'.format(coordinator.config_entry.title, suffix)

    @property
    def name(self) -> str:
        return self._name
