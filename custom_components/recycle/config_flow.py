"""Config flow for Recycle! integration."""

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ApiClient, ApiAddress

from .const import (
    CONF_ZIPCODE,
    CONF_CITY_ID,
    CONF_STREET_ID,
    CONF_HOUSE_NR,
    CONF_COLLECTIONS_TIMEFRAME,
    CONF_FRACTIONS_IGNORE,
    COLLECTIONS_TIMEFRAME,
    DOMAIN,
)

CONF_FRACTIONS_FILTER = "fractions_filter"


async def _validate_address(hass: HomeAssistant, address: ApiAddress) -> bool:
    """Validate the Recycle! address"""
    session = async_get_clientsession(hass)
    client = ApiClient(session)
    return await client.validate_address(address)


async def _get_fractions(hass: HomeAssistant, address: ApiAddress):
    """Get the possible fractions"""
    session = async_get_clientsession(hass)
    client = ApiClient(session)
    return await client.get_fractions(address)


def suggested(value: any) -> dict[str, any]:
    return {'suggested_value': value}


class RecycleConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle config flow for Recycle!"""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, any] = None) -> FlowResult:
        """Invoked when a user initiates a flow via the user interface"""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not await _validate_address(self.hass, ApiAddress(
                    zipcode=user_input.get(CONF_ZIPCODE),
                    city_id=user_input.get(CONF_CITY_ID),
                    street_id=user_input.get(CONF_STREET_ID),
                    house_nr=user_input.get(CONF_HOUSE_NR),
            )):
                errors['base'] = 'address'

            if not errors:
                name = user_input.get(CONF_NAME)
                data = {
                    CONF_ZIPCODE: user_input.get(CONF_ZIPCODE),
                    CONF_CITY_ID: user_input.get(CONF_CITY_ID),
                    CONF_STREET_ID: user_input.get(CONF_STREET_ID),
                    CONF_HOUSE_NR: user_input.get(CONF_HOUSE_NR),
                    CONF_LATITUDE: user_input.get(CONF_LATITUDE) or None,
                    CONF_LONGITUDE: user_input.get(CONF_LONGITUDE) or None,
                }
                unique_id = '{}-{}-{}-{}'.format(
                    user_input.get(CONF_ZIPCODE),
                    user_input.get(CONF_CITY_ID),
                    user_input.get(CONF_STREET_ID),
                    user_input.get(CONF_HOUSE_NR),
                )

                await self.async_set_unique_id(unique_id=unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=name, data=data)
        else:
            user_input = {}

        default_name = 'Recycle {}'.format(self.hass.config.location_name)
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, description=suggested(user_input.get(CONF_NAME, default_name))): cv.string,
                vol.Required(CONF_ZIPCODE, description=suggested(user_input.get(CONF_ZIPCODE))): cv.positive_int,
                vol.Required(CONF_CITY_ID, description=suggested(user_input.get(CONF_CITY_ID))): cv.positive_int,
                vol.Required(CONF_STREET_ID, description=suggested(user_input.get(CONF_STREET_ID))): cv.positive_int,
                vol.Required(CONF_HOUSE_NR, description=suggested(user_input.get(CONF_HOUSE_NR))): cv.positive_int,
                vol.Optional(CONF_LATITUDE, description=suggested(user_input.get(CONF_LATITUDE, self.hass.config.latitude)), default=0): cv.latitude,
                vol.Optional(CONF_LONGITUDE, description=suggested(user_input.get(CONF_LONGITUDE, self.hass.config.longitude)), default=0): cv.longitude,
            }
        )

        return self.async_show_form(step_id='user', data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        return RecycleOptionFlowHandler(config_entry)


class RecycleOptionFlowHandler(OptionsFlow):
    """Handles options flow for the Recycle! component"""

    def __init__(self, entry: ConfigEntry) -> None:
        """Manage the Recycle! component options"""
        super().__init__()
        self.config_entry: ConfigEntry = entry
        self.fractions: dict[str, str] = {}

    async def async_step_init(self, user_input: dict[str, any] = None) -> FlowResult:
        """Manage the Recycle! component options"""

        fractions_api = await _get_fractions(self.hass, ApiAddress(
            zipcode=self.config_entry.data.get(CONF_ZIPCODE),
            city_id=self.config_entry.data.get(CONF_CITY_ID),
            street_id=self.config_entry.data.get(CONF_STREET_ID),
            house_nr=self.config_entry.data.get(CONF_HOUSE_NR),
        ))
        self.fractions = {
            fraction.id: fraction.name
            for fraction in fractions_api
        }

        return await self.async_step_user()

    async def async_step_user(self, user_input: dict[str, any] = None) -> FlowResult:
        if user_input is not None:
            options = {
                CONF_FRACTIONS_IGNORE: list(self.fractions.keys() - user_input.get(CONF_FRACTIONS_FILTER, [])),
                CONF_COLLECTIONS_TIMEFRAME: user_input.get(CONF_COLLECTIONS_TIMEFRAME),
            }

            return self.async_create_entry(title='', data=options)

        fractions_filter = list(self.fractions.keys() - self.config_entry.options.get(CONF_FRACTIONS_IGNORE, []))

        data_schema = vol.Schema({
            # @TODO add language selection
            vol.Optional(
                CONF_FRACTIONS_FILTER,
                description=suggested(fractions_filter)
            ): cv.multi_select(self.fractions),
            vol.Optional(
                CONF_COLLECTIONS_TIMEFRAME,
                default=COLLECTIONS_TIMEFRAME,
                description=suggested(self.config_entry.options.get(CONF_COLLECTIONS_TIMEFRAME))
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=70)),
        })

        return self.async_show_form(step_id='user', data_schema=data_schema, errors={})
