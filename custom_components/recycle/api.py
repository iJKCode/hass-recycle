from datetime import date, datetime, timedelta
from typing import Any

from dateutil import parser
import pytz

import aiohttp

API_URL_BASE = 'https://recycleapp.be/api/app/v1/'
API_STREET_BASE = 'https://data.vlaanderen.be/id/straatnaam-'
API_X_SECRET = "Crgja3EGWe8jdapyr4EEoMBgZACYYjRRcRpaMQrLDW9HJBvmgkfGQyYqLgeXPavAGvnJqkV87PBB2b8zx43q46sUgzqio4yRZbABhtKeagkVKypTEDjKfPgGycjLyJTtLHYpzwJgp4YmmCuJZN9ZmJY8CGEoFs8MKfdJpU9RjkEVfngmmk2LYD4QzFegLNKUbcCeAdEW"
API_X_CONSUMER = "recycleapp.be"
API_USER_AGENT = "Home Assistant"


class Api:
    def __init__(self, session: aiohttp.ClientSession, language: str = 'nl'):
        self.language = language
        self._session = session
        self._cached_token: str = ''
        self._cached_expiry: datetime = datetime.utcfromtimestamp(0)

    async def get_about(self):
        return await self.get_endpoint('about')

    async def get_faq(self, organisation_id: str):
        return await self.get_endpoint('faq', {
            'organisation': organisation_id
        })

    # ------ Address API --------------------------------------------------------- #

    async def validate_address(self, info: ApiAddress):
        token = await self.get_token()
        headers = self.get_headers(token)
        params = self._address_params(info)
        async with self._session.head(API_URL_BASE + 'streets/validate', params=params, headers=headers, raise_for_status=False) as request:
            return 200 <= request.status < 300

    async def get_collections(self, info: ApiAddress, *, limit: int = 50, page: int = 1, date_from: date = None, date_until: date = None):
        if date_from is None:
            date_from = date.today()
        if date_until is None:
            date_until = date_from + timedelta(weeks=1)

        return await self.get_endpoint('collections', {
            'zipcodeId': str(info.zipcode) + '-' + str(info.town_id),
            'streetId': API_STREET_BASE + str(info.street_id),
            'houseNumber': info.house_nr,
            'fromDate': date_from.strftime('%Y-%m-%d'),
            'untilDate': date_until.strftime('%Y-%m-%d'),
        }, limit, page)

    async def get_fractions(self, info: ApiAddress, *, limit: int = 50, page: int = 1):
        return await self.get_endpoint('fractions', self._address_params(info), limit, page)

    async def get_organisations(self, info: ApiAddress):
        return await self.get_endpoint('organisations/' + str(info.zipcode) + '-' + str(info.town_id))

    async def get_communications(self, info: ApiAddress, *, limit: int = 50, page: int = 1):
        return await self.get_endpoint('communications', self._address_params(info), limit, page)

    async def get_communication(self, communication_id: str):
        return await self.get_endpoint('communications/' + communication_id)

    async def get_campaign(self, info: ApiAddress):
        return await self.get_endpoint('communications/campaign', self._address_params(info))

    async def get_fact(self, info: ApiAddress):
        return await self.get_endpoint('communications/fact', self._address_params(info))

    @staticmethod
    def _address_params(info: ApiAddress):
        return {
            'zipcodeId': str(info.zipcode) + '-' + str(info.town_id),
            'streetId': API_STREET_BASE + str(info.street_id),
            'houseNumber': info.house_nr,
        }

    # ------ Location API -------------------------------------------------------- #

    async def get_collection_points(self, info: ApiAddress, *, limit: int = 50, page: int = 1):
        return await self.get_endpoint('collection-points', self._location_params(info), limit, page)

    async def get_collection_point_types(self):
        return await self.get_endpoint('collection-point-types')

    async def get_recycling_parks(self, info: ApiAddress, *, limit: int = 50, page: int = 1, longitude: float = None, latitude: float = None, radius: int = 5000):
        return await self.get_endpoint('collection-points/recycling-parks', self._location_params(info, longitude, latitude, radius), limit, page)

    @staticmethod
    def _location_params(info: ApiAddress, longitude: float = None, latitude: float = None, radius: int = None):
        has_lat_long = info.latitude is not None and info.longitude is not None
        return {
            'zipcode': str(info.zipcode) + '-' + str(info.town_id),
            'latitude': info.latitude if has_lat_long else None,
            'longitude': info.longitude if has_lat_long else None,
            'radius': radius if has_lat_long else None,
        }

    # ------ Endpoint Abstraction ------------------------------------------------ #

    async def get_endpoint(self, endpoint: str, params=None, limit: int = None, page: int = None) -> Any:
        if limit is not None:
            params['size'] = limit if limit is not None else 200
        if page is not None:
            params['page'] = page

        token = await self.get_token()
        headers = self.get_headers(token)
        return await self._get_json(API_URL_BASE + endpoint, params=params, headers=headers)

    def get_headers(self, token: str) -> dict[str, str]:
        return {
            'User-Agent': API_USER_AGENT,
            'Authorization': token,
            'X-Consumer': API_X_CONSUMER,
        }

    async def get_token(self, renew: bool = False) -> str:
        # check if cached token is still valid
        if self._cached_token and pytz.utc.localize(datetime.utcnow()) < self._cached_expiry and not renew:
            return self._cached_token

        # request new token
        headers = {
            'User-Agent': API_USER_AGENT,
            'X-Secret': API_X_SECRET,
            'X-Consumer': API_X_CONSUMER,
        }
        response = await self._get_json(API_URL_BASE + 'access-token', headers=headers)

        # update cached token and expiry info
        self._cached_token = response['accessToken']
        self._cached_expiry = parser.parse(response['expiresAt']) - timedelta(minutes=5)

        return self._cached_token

    async def _get_json(self, url: str, *, params=None, headers=None, raise_for_status=True, **kwargs) -> Any:
        async with self._session.get(url, params=params, headers=headers, raise_for_status=raise_for_status, **kwargs) as request:
            return await request.json() if request.content else None
