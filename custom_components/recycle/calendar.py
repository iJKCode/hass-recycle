"""Recycle! integration calendar."""
import logging
from datetime import date, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api_model import Collection
from .const import DOMAIN
from .coordinator import RecycleCoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Set up Recycle! calendars from a config entry."""
    _LOGGER.debug('Setting up calendar config entry: %s', entry.unique_id)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        RecycleCalendar(coordinator)
    ])
    return True


class RecycleCalendar(RecycleCoordinatorEntity, CalendarEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, name_suffix='Collections', id_suffix='collections')
        self._collection = self.coordinator.collections[0] if self.coordinator.collections else None

    def _handle_coordinator_update(self) -> None:
        self._collection = self.coordinator.collections[0] if self.coordinator.collections else None
        super()._handle_coordinator_update()

    @property
    def event(self):
        return self._make_event(self._collection) if self._collection else None

    async def async_get_events(self, hass, start_date: date, end_date: date) -> list[CalendarEvent]:
        _LOGGER.debug(
            'Fetching calendar events for %s between %s and %s',
            self.entity_id, start_date.isoformat(), end_date.isoformat()
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
    def _make_event(collection: Collection) -> CalendarEvent:
        title = collection.fraction.name
        return CalendarEvent(
            summary=title.capitalize() if title.islower() else title,
            start=collection.timestamp,
            end=collection.timestamp + timedelta(days=1),
        )
