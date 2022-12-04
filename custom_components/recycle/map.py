"""Recycle! integration map markers."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Set up Recycle! map markers from a config entry."""
    _LOGGER.debug('Setting up map config entry: %s', entry.unique_id)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([])
    return True

# @TODO collection point map markers
