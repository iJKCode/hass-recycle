"""Recycle! integration constants."""
from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "recycle"

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]

SCAN_INTERVAL = timedelta(hours=1)
COLLECTIONS_TIMEFRAME = 14  # Days
FORECAST_SENSOR_COUNT = 6

CONF_ZIPCODE = "zipcode"
CONF_CITY_ID = "city_id"
CONF_STREET_ID = "street_id"
CONF_HOUSE_NR = "house_nr"

CONF_COLLECTIONS_TIMEFRAME = "collections_timeframe"
CONF_FRACTIONS_IGNORE = "fractions_ignore"
