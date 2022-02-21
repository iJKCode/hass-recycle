"""Recycle! integration sensors."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Set up Recycle! sensors from a config entry."""
    _LOGGER.debug('Setting up sensors config entry: %s', entry.unique_id)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([])
    return True
