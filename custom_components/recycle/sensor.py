"""Recycle! integration sensors."""

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Recycle! sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([], update_before_add=True)
