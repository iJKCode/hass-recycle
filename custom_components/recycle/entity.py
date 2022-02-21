"""Recycle! integration base entity."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .api import ApiClient, ApiAddress
from .api_model import Collection, Fraction, Communication
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, DEFAULT_COLLECTIONS_TIMEFRAME

_LOGGER = logging.getLogger(__name__)


class RecycleDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Class to manage fetching Recycle! api data."""

    def __init__(
            self,
            hass: HomeAssistant,
            api_client: ApiClient,
            api_address: ApiAddress,
            update_interval: timedelta = DEFAULT_SCAN_INTERVAL,
            collections_timeframe: int = DEFAULT_COLLECTIONS_TIMEFRAME,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)
        self.api_client = api_client
        self.api_address = api_address
        self.collections_timeframe = collections_timeframe

        self.collections: list[Collection] = []
        self.fractions: dict[str, Fraction] = {}
        self.communications: list[Communication] = []

    async def _async_update_data(self) -> None:
        """Update data from Recycle! api."""
        _LOGGER.debug('Fetching recycle information for: {}'.format(self.config_entry.entry_id))

        timeframe = timedelta(days=self.collections_timeframe)
        self.collections = await self.api_client.get_collections(self.api_address, time_delta=timeframe)

        return None


class RecycleCoordinatorEntity(CoordinatorEntity):
    coordinator: RecycleDataUpdateCoordinator

    def __init__(self, coordinator: RecycleDataUpdateCoordinator, suffix: str, unique_id: str = None):
        super().__init__(coordinator)
        self._attr_name = '{} {}'.format(coordinator.config_entry.title, suffix)
        self._attr_unique_id = '{}-{}'.format(coordinator.config_entry.unique_id, unique_id or suffix.lower())
