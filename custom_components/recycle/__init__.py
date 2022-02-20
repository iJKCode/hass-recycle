"""The Recycle! integration."""

from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .entity import RecycleDataUpdateCoordinator
from .const import (
    SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
    PLATFORMS,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Recycle! component."""
    # @TODO: Add setup code.
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recycle! component from a config entry."""
    LOGGER.debug("Setting up config entry: %s", entry.unique_id)

    session = async_get_clientsession(hass)
    coordinator = RecycleDataUpdateCoordinator(hass, session, SCAN_INTERVAL, None)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Recycle! component from a config entry."""
    LOGGER.debug("Unloading config entry: %s", entry.unique_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        del hass.data[DOMAIN][entry.entry_id]
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update Recycle! component options"""
    await hass.config_entries.async_reload(entry.entry_id)
