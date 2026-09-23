from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchQuery:
    text: str


@dataclass(frozen=True)
class TrackMetadata:
    provider_track_id: str
    title: str
    artist: str
    album: str
    release_year: str
    duration_seconds: int
    cover_image_url: str | None
    external_url: str


class MusicSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: SearchQuery) -> list[TrackMetadata]:
        ...
