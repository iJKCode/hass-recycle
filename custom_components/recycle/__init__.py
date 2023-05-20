"""Recycle! integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ApiClient, ApiAddress
from .coordinator import RecycleDataUpdateCoordinator
from .const import (
    CONF_ZIPCODE,
    CONF_CITY_ID,
    CONF_STREET_ID,
    CONF_HOUSE_NR,
    CONF_COLLECTIONS_TIMEFRAME,
    CONF_FRACTIONS_IGNORE,
    COLLECTIONS_TIMEFRAME,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recycle! component from a config entry."""
    _LOGGER.debug('Setting up config entry: %s', entry.unique_id)

    session = async_get_clientsession(hass)
    client = ApiClient(session=session)
    address = ApiAddress(
        zipcode=entry.data.get(CONF_ZIPCODE),
        city_id=entry.data.get(CONF_CITY_ID),
        street_id=entry.data.get(CONF_STREET_ID),
        house_nr=entry.data.get(CONF_HOUSE_NR),
        latitude=entry.data.get(CONF_LATITUDE),
        longitude=entry.data.get(CONF_LONGITUDE),
    )

    coordinator = RecycleDataUpdateCoordinator(
        hass, api_client=client, api_address=address,
        fractions_ignore=entry.options.get(CONF_FRACTIONS_IGNORE, []),
        collections_timeframe=entry.options.get(CONF_COLLECTIONS_TIMEFRAME),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Recycle! component from a config entry."""
    _LOGGER.debug('Unloading config entry: %s', entry.title)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        del hass.data[DOMAIN][entry.entry_id]

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update Recycle! component options."""
    _LOGGER.debug('Updating config options: %s', entry.title)
    await hass.config_entries.async_reload(entry.entry_id)
