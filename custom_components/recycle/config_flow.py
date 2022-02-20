"""Config flow for Recycle! integration."""

from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow, HANDLERS
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_SCAN_INTERVAL, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import Api, ApiAddress

from .const import (
    CONF_ZIPCODE,
    CONF_TOWN_ID,
    CONF_STREET_ID,
    CONF_HOUSE_NR,
    DOMAIN,
)


async def validate_address(user_input: dict[str, Any], hass: HomeAssistant) -> bool:
    """Validate the Recycle! address"""
    session = async_get_clientsession(hass)
    api = Api(session)
    addr = ApiAddress(
        zipcode=user_input.get(CONF_ZIPCODE),
        town_id=user_input.get(CONF_TOWN_ID),
        street_id=user_input.get(CONF_STREET_ID),
        house_nr=user_input.get(CONF_HOUSE_NR),
    )
    return await api.validate_address(addr)


class RecycleConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle config flow for Recycle!"""

    VERSION = 1

    async def async_step_user(self, user_input: Dict[str, Any] = None) -> FlowResult:
        """Invoked when a user initiates a flow via the user interface"""
        errors: Dict[str, str] = {}
        if user_input is not None:
            if not await validate_address(user_input, self.hass):
                errors['base'] = 'address'

            if not errors:
                name = user_input.get(CONF_NAME)
                return self.async_create_entry(title=name, data=user_input)
        else:
            user_input = {}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=user_input.get(CONF_NAME, self.hass.config.location_name)): cv.string,
                vol.Required(CONF_ZIPCODE, default=user_input.get(CONF_ZIPCODE)): cv.positive_int,
                vol.Required(CONF_TOWN_ID, default=user_input.get(CONF_TOWN_ID)): cv.positive_int,
                vol.Required(CONF_STREET_ID, default=user_input.get(CONF_STREET_ID)): cv.positive_int,
                vol.Required(CONF_HOUSE_NR, default=user_input.get(CONF_HOUSE_NR)): cv.positive_int,
                vol.Optional(CONF_LATITUDE, default=user_input.get(CONF_LATITUDE, self.hass.config.latitude)): cv.latitude,
                vol.Optional(CONF_LONGITUDE, default=user_input.get(CONF_LONGITUDE, self.hass.config.longitude)): cv.longitude,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        return RecycleOptionFlowHandler(config_entry)


class RecycleOptionFlowHandler(OptionsFlow):
    """Handles options flow for the Recycle! component"""

    def __init__(self, entry: ConfigEntry) -> None:
        """Manage the Recycle! component options"""
        super().__init__()
        self.config_entry = entry

    async def async_step_init(self, user_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """Manage the Recycle! component options"""
        return await self.async_step_user()

    async def async_step_user(self, user_input: dict[str, Any] = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title='', data=user_input)

        data_schema = vol.Schema({
            # @TODO add fraction filter options
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors={})
