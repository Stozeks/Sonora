from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchQuery:
    text: str


@dataclass(frozen=True)
class TrackMetadata:
    title: str
    artist: str


class MusicSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: SearchQuery) -> list[TrackMetadata]:
        """Search track metadata for a user query."""
