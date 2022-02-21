"""Recycle! integration calendar."""
import logging
from datetime import date

from homeassistant.components.calendar import CalendarEventDevice
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api_model import Collection
from .const import DOMAIN, EVENT_DATE_FORMAT
from .entity import RecycleCoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Set up Recycle! calendars from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        RecycleCalendarDevice(coordinator)
    ])
    return True


class RecycleCalendarDevice(RecycleCoordinatorEntity, CalendarEventDevice):
    def __init__(self, coordinator):
        super().__init__(coordinator, suffix='Collections')

    @property
    def event(self):
        collections = self.coordinator.collections
        return self._make_event(collections[1]) if collections else None

    async def async_get_events(self, hass, start_date: date, end_date: date) -> list[dict[str, any]]:
        _LOGGER.debug('Fetching calendar events for %s between %s and %s', self.entity_id, start_date.strftime(EVENT_DATE_FORMAT), end_date.strftime(EVENT_DATE_FORMAT))

        address = self.coordinator.api_address
        client = self.coordinator.api_client

        collections = await client.get_collections(address, start_date=start_date, end_date=end_date)
        return [self._make_event(collection) for collection in collections]

    @staticmethod
    def _make_event(collection: Collection) -> dict[str, any]:
        event_date = {'date': collection.timestamp.strftime(EVENT_DATE_FORMAT)}
        return {
            'uid': collection.id,
            'summary': collection.fraction.name,
            'start': event_date,
            'end': event_date,
            'allDay': True,
        }
