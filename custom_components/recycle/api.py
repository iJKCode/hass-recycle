"""Recycle! api wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from aiohttp import ClientSession
from dateutil import parser
import pytz

from .api_model import Collection, Fraction

API_URL_BASE = 'https://recycleapp.be/api/app/v1/'
API_STREET_BASE = 'https://data.vlaanderen.be/id/straatnaam-{}'
API_X_SECRET = "Crgja3EGWe8jdapyr4EEoMBgZACYYjRRcRpaMQrLDW9HJBvmgkfGQyYqLgeXPavAGvnJqkV87PBB2b8zx43q46sUgzqio4yRZbABhtKeagkVKypTEDjKfPgGycjLyJTtLHYpzwJgp4YmmCuJZN9ZmJY8CGEoFs8MKfdJpU9RjkEVfngmmk2LYD4QzFegLNKUbcCeAdEW"
API_X_CONSUMER = "recycleapp.be"
API_USER_AGENT = "Home Assistant"


@dataclass(frozen=True)
class ApiAddress:
    zipcode: int
    city_id: int
    street_id: int
    house_nr: int
    latitude: float | None = None
    longitude: float | None = None


class ApiClient:
    def __init__(self, session: ClientSession):
        self._session: ClientSession = session
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
        headers = self._headers(token)
        params = self._address_params(info)
        async with self._session.head(API_URL_BASE + 'streets/validate', params=params, headers=headers, raise_for_status=False) as request:
            return 200 <= request.status < 300

    async def get_collections(
            self, info: ApiAddress, *, limit: int = 50, page: int = 1,
            start_date: date = None, end_date: date = None, time_delta: timedelta = None
    ) -> list[Collection]:
        if start_date is None:
            if time_delta is not None and end_date is not None:
                start_date = end_date - time_delta
            else:
                start_date = date.today()
        if end_date is None:
            if time_delta is None:
                time_delta = timedelta(weeks=2)
            end_date = start_date + time_delta

        collections_json = await self.get_endpoint('collections', {
            **self._address_params(info),
            'fromDate': start_date.strftime('%Y-%m-%d'),
            'untilDate': end_date.strftime('%Y-%m-%d'),
        }, limit, page)

        return sorted(
            [Collection(  # @TODO language selection
                id=collection['id'],
                type=collection['type'],
                timestamp=parser.parse(collection['timestamp']).date(),
                fraction=Fraction(
                    id=collection['fraction']['id'],
                    name=collection['fraction']['name']['nl'],  # @TODO language
                    logos=[],  # @TODO logos
                    color=collection['fraction']['color'],
                    organisation_id=collection['fraction']['organisation'],
                )
            ) for collection in collections_json['items']],
            key=lambda item: item.timestamp
        )

    async def get_fractions(self, info: ApiAddress, *, limit: int = 50, page: int = 1):
        fractions_json = await self.get_endpoint('fractions', self._address_params(info), limit, page)
        return [Fraction(
            id=fraction['id'],
            name=fraction['name']['nl'],  # @TODO language
            logos=[],  # @TODO logos
            color=fraction['color'],
        ) for fraction in fractions_json['items']]

    async def get_organisations(self, info: ApiAddress):
        return await self.get_endpoint('organisations/{}-{}'.format(info.zipcode, info.city_id))

    async def get_communications(self, info: ApiAddress, *, limit: int = 50, page: int = 1):
        return await self.get_endpoint('communications', self._address_params(info), limit, page)

    async def get_communication(self, communication_id: str):
        return await self.get_endpoint('communications/{}'.format(communication_id))

    async def get_campaign(self, info: ApiAddress):
        return await self.get_endpoint('communications/campaign', self._address_params(info))

    async def get_fact(self, info: ApiAddress):
        return await self.get_endpoint('communications/fact', self._address_params(info))

    @staticmethod
    def _address_params(info: ApiAddress):
        return {
            'zipcodeId': '{}-{}'.format(info.zipcode, info.city_id),
            'streetId': API_STREET_BASE.format(info.street_id),
            'houseNumber': info.house_nr,
        }

    # ------ Location API -------------------------------------------------------- #

    async def get_collection_points(self, info: ApiAddress, *, limit: int = 50, page: int = 1):
        return await self.get_endpoint('collection-points', self._location_params(info), limit, page)

    async def get_collection_point_types(self):
        return await self.get_endpoint('collection-point-types')

    async def get_recycling_parks(self, info: ApiAddress, *, limit: int = 50, page: int = 1, radius: int = 5000):
        return await self.get_endpoint('collection-points/recycling-parks', self._location_params(info, radius), limit, page)

    @staticmethod
    def _location_params(info: ApiAddress, radius: int = None):
        has_lat_long = info.latitude is not None and info.longitude is not None
        return {
            'zipcode': '{}-{}'.format(info.zipcode, info.city_id),
            'latitude': info.latitude if has_lat_long else None,
            'longitude': info.longitude if has_lat_long else None,
            'radius': radius if has_lat_long else None,
        }

    # ------ Endpoint Abstraction ------------------------------------------------ #

    async def get_endpoint(self, endpoint: str, params: dict[str, any] | None = None, limit: int = None, page: int = None) -> any:
        if limit is not None:
            params['size'] = limit if limit < 200 else 200
        if page is not None:
            params['page'] = page

        token = await self.get_token()
        headers = self._headers(token)
        return await self._request(API_URL_BASE + endpoint, params=params, headers=headers)

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
        response = await self._request(API_URL_BASE + 'access-token', headers=headers)

        # update cached token and expiry info
        self._cached_token = response['accessToken']
        self._cached_expiry = parser.parse(response['expiresAt']) - timedelta(minutes=5)

        return self._cached_token

    @staticmethod
    def _headers(token: str) -> dict[str, str]:
        return {
            'User-Agent': API_USER_AGENT,
            'Authorization': token,
            'X-Consumer': API_X_CONSUMER,
        }

    async def _request(self, url: str, *, params: dict[str, any] | None = None, headers=None, raise_for_status=True, **kwargs) -> any:
        params = {k: v for k, v in params.items() if v is not None} if params else {}
        async with self._session.get(url, params=params, headers=headers, raise_for_status=raise_for_status, **kwargs) as request:
            return await request.json() if request.content else None
