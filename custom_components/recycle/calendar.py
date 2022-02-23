"""Recycle! integration calendar."""
import logging
from datetime import date, timedelta

from homeassistant.components.calendar import CalendarEventDevice
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import DATE_STR_FORMAT

from .api_model import Collection
from .const import DOMAIN
from .entity import RecycleCoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Set up Recycle! calendars from a config entry."""
    _LOGGER.debug('Setting up calendar config entry: %s', entry.unique_id)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        RecycleCalendarDevice(coordinator)
    ])
    return True


class RecycleCalendarDevice(RecycleCoordinatorEntity, CalendarEventDevice):
    def __init__(self, coordinator):
        super().__init__(coordinator, suffix='Collections', unique_id='collections')

    @property
    def event(self):
        collections = self.coordinator.collections
        return self._make_event(collections[0]) if collections else None

    async def async_get_events(self, hass, start_date: date, end_date: date) -> list[dict[str, any]]:
        _LOGGER.debug(
            'Fetching calendar events for %s between %s and %s',
            self.entity_id, start_date.strftime(DATE_STR_FORMAT), end_date.strftime(DATE_STR_FORMAT)
        )

        address = self.coordinator.api_address
        client = self.coordinator.api_client

        collections = await client.get_collections(address, start_date=start_date, end_date=end_date)
        return [
            self._make_event(collection)
            for collection in collections
            if collection.fraction.id not in self.coordinator.fractions_ignore
        ]

    @staticmethod
    def _make_event(collection: Collection) -> dict[str, any]:
        start_date = collection.timestamp
        end_date = collection.timestamp + timedelta(days=1)
        return {
            'uid': collection.id,
            'summary': collection.fraction.name,
            'start': {'date': start_date.strftime(DATE_STR_FORMAT)},
            'end': {'date': end_date.strftime(DATE_STR_FORMAT)},
            'allDay': True,
        }
