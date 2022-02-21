"""Recycle! integration constants."""
from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "recycle"

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]

DEFAULT_SCAN_INTERVAL = timedelta(hours=1)
DEFAULT_COLLECTIONS_TIMEFRAME = 14  # Days

CONF_ZIPCODE = "zipcode"
CONF_CITY_ID = "city_id"
CONF_STREET_ID = "street_id"
CONF_HOUSE_NR = "house_nr"

CONF_COLLECTIONS_TIMEFRAME = "collections_timeframe"

EVENT_DATE_FORMAT = "%Y-%m-%d"
