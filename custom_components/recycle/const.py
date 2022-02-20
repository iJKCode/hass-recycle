"""Constants for the Recycle! integration."""

import logging
from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "recycle"

PLATFORMS = [Platform.SENSOR]

LOGGER = logging.getLogger(__package__)

SCAN_INTERVAL = timedelta(hours=1)

CONF_ZIPCODE = "zipcode"
CONF_TOWN_ID = "town_id"
CONF_STREET_ID = "street_id"
CONF_HOUSE_NR = "house_nr"
