"""Recycle! api models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Language(Enum):
    NL = 'nl'
    FR = 'fr'
    EN = 'en'
    DE = 'de'


@dataclass(frozen=True)
class Image:
    id: str
    scale: int


@dataclass(frozen=True)
class ZipCodeId:
    zipcode: int
    city_id: int


@dataclass(frozen=True)
class Organisation:
    id: str
    name: str
    short_name: str
    url: str
    logos: list[Image]
    description: str
    zipcode_ids: list[ZipCodeId]
    isIC: bool
    olympusId: int
    projectId: int


# ====== COLLECTIONS ========================================================= #

@dataclass(frozen=True)
class Variation:
    pass  # @TODO variation dataclass


@dataclass(frozen=True)
class Fraction:
    id: str
    name: str
    logos: list[Image]
    color: str
    national: bool | None = field(default=None)
    organisation_id: str | None = field(default=None)
    variations: list[Variation] = field(default_factory=list)


@dataclass(frozen=True)
class Collection:
    id: str
    type: str
    fraction: Fraction
    timestamp: date


# ====== COLLECTION POINTS =================================================== #

@dataclass(frozen=True)
class CollectionPointType:
    id: str
    key: str
    name: str
    admin: bool


@dataclass(frozen=True)
class CollectionPointInfo:
    pass  # @TODO collection point info (recycling park)


@dataclass(frozen=True)
class CollectionPointTargetCity:
    id: int
    name: str
    zipcode_ids: list[ZipCodeId]


@dataclass(frozen=True)
class CollectionPointTarget:
    code: int
    names: list[str]
    cities: list[CollectionPointTargetCity]
    zipcode_id: ZipCodeId


@dataclass(frozen=True)
class CollectionPoint:
    id: str
    name: str
    type: CollectionPointType
    targets: list[CollectionPointTarget]
    link: str | None
    city: str
    street: str
    house_nr: int
    zipcode: int
    latitude: float
    longitude: float
    display_name: str
    active: bool
    source: str
    # @TODO opening hours & exception days


# ====== COMMUNICATIONS ====================================================== #

@dataclass(frozen=True)
class Communication:
    id: str
    type: str
    title: str
    preview: str
    content: str
    images: list[Image]
    publish_date: date
    expiry_date: date


@dataclass(frozen=True)
class CommunicationCampaign:
    pass  # @TODO communication campaign


@dataclass(frozen=True)
class CommunicationFact:
    pass  # @TODO communication fact


# ====== ABOUT =============================================================== #

@dataclass(frozen=True)
class AboutPartner:
    url: str
    logos: list[Image]


@dataclass(frozen=True)
class About:
    description: str
    partners: list[AboutPartner]


@dataclass(frozen=True)
class Faq:
    pass  # @TODO about faq
