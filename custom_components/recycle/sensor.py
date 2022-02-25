"""Recycle! integration sensors."""
from __future__ import annotations

import logging
from datetime import date, timedelta

from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_NAME, ATTR_DATE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .api_model import Collection, Fraction
from .const import DOMAIN, CONF_FRACTIONS_IGNORE, FORECAST_SENSOR_COUNT
from .entity import RecycleCoordinatorEntity, RecycleDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

STATE_NO_COLLECTION = 'No collection'
RELATIVE_DATE_TODAY = 'today'
RELATIVE_DATE_TOMORROW = 'tomorrow'
RELATIVE_DATE_TEMPLATE = 'in {} days'


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Set up Recycle! sensors from a config entry."""
    _LOGGER.debug('Setting up sensors config entry: %s', entry.unique_id)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        TodayCollectionSensor(coordinator),
        TomorrowCollectionSensor(coordinator),
        UpcomingCollectionSensor(coordinator),
        *[
            IndexCollectionSensor(coordinator, collection_index=index)
            for index in range(0, FORECAST_SENSOR_COUNT)
        ],
        *[
            FractionCollectionSensor(coordinator, fraction=fraction)
            for fraction in coordinator.fractions
            if fraction.id not in entry.options.get(CONF_FRACTIONS_IGNORE, [])
        ]
    ])
    return True


class CollectionSensor(RecycleCoordinatorEntity):
    def __init__(self, coordinator: RecycleDataUpdateCoordinator, name_suffix: str, id_suffix: str = None):
        super().__init__(
            coordinator,
            id_suffix=id_suffix,
            name_suffix=name_suffix,
            entity_id_format=ENTITY_ID_FORMAT,
        )
        self._collection = None

    def _get_collection(self) -> Collection | None:
        raise NotImplementedError()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._collection = self._get_collection()
        super()._handle_coordinator_update()

    @staticmethod
    def _relative_date(collection_date: date):
        days = (collection_date - date.today()).days
        if days == 0:
            return RELATIVE_DATE_TODAY
        elif days == 1:
            return RELATIVE_DATE_TOMORROW
        else:
            return RELATIVE_DATE_TEMPLATE.format(days)

    @staticmethod
    def _capitalize(text: str):
        return text.capitalize() if text.islower() else text

    @property
    def state(self) -> StateType:
        if self._collection is None:
            return STATE_NO_COLLECTION
        return self._capitalize('{} {}'.format(
            self._collection.fraction.name,
            self._relative_date(self._collection.timestamp),
        ))

    @property
    def state_attributes(self) -> dict[str, any] | None:
        return {
            ATTR_NAME: self._collection.fraction.name if self._collection else None,
            ATTR_DATE: self._collection.timestamp.isoformat() if self._collection else None,
        }


class TodayCollectionSensor(CollectionSensor):
    def __init__(self, coordinator: RecycleDataUpdateCoordinator):
        super().__init__(
            coordinator,
            id_suffix='collection_today',
            name_suffix='Collection Today',
        )
        self._collection = self._get_collection()

    def _get_collection(self) -> Collection | None:
        if self.coordinator.collections:
            tomorrow = date.today() + timedelta(days=1)
            collection = self.coordinator.collections[0]
            if collection and collection.timestamp < tomorrow:
                return collection
        return None


class TomorrowCollectionSensor(CollectionSensor):
    def __init__(self, coordinator: RecycleDataUpdateCoordinator):
        super().__init__(
            coordinator,
            id_suffix='collection_tomorrow',
            name_suffix='Collection Tomorrow',
        )
        self._collection = self._get_collection()

    def _get_collection(self) -> Collection | None:
        if self.coordinator.collections:
            date_start = date.today() + timedelta(days=1)
            date_stop = date.today() + timedelta(days=2)
            collection = self.coordinator.collections[0]
            if collection and date_start < collection.timestamp < date_stop:
                return collection
        return None


class UpcomingCollectionSensor(CollectionSensor):
    def __init__(self, coordinator: RecycleDataUpdateCoordinator):
        super().__init__(
            coordinator,
            id_suffix='collection_upcoming',
            name_suffix='Upcoming Collection',
        )
        self._collection = self._get_collection()

    def _get_collection(self) -> Collection | None:
        today = date.today()
        for collection in self.coordinator.collections:
            if collection.timestamp > today:
                return collection
        return None


class FractionCollectionSensor(CollectionSensor):
    def __init__(self, coordinator: RecycleDataUpdateCoordinator, fraction: Fraction):
        super().__init__(
            coordinator,
            id_suffix='fraction_{}'.format(fraction.id),
            name_suffix='Fraction {}'.format(
                self._capitalize(fraction.name)
            ),
        )
        self._fraction = fraction
        self._collection = self._get_collection()

    def _get_collection(self) -> Collection | None:
        for collection in self.coordinator.collections:
            if collection.fraction.id == self._fraction.id:
                return collection
        return None


class IndexCollectionSensor(CollectionSensor):
    def __init__(self, coordinator: RecycleDataUpdateCoordinator, collection_index: int):
        super().__init__(
            coordinator,
            id_suffix='forecast_{}'.format(collection_index),
            name_suffix='Forecast {}'.format(collection_index),
        )
        self._collection_index = collection_index
        self._collection = self._get_collection()

    def _get_collection(self) -> Collection | None:
        try:
            return self.coordinator.collections[self._collection_index]
        except IndexError:
            return None

    @property
    def name(self) -> str:
        return self._capitalize(self._collection.fraction.name) if self._collection else ''

    @property
    def state(self) -> StateType:
        return self._capitalize(self._relative_date(self._collection.timestamp) if self._collection else '')

    @property
    def icon(self) -> str | None:
        return '' if self._collection else 'mdi:none'  # @TODO select icon
