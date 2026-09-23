from __future__ import annotations

import time
from collections import OrderedDict

from bot.providers.base import TrackMetadata


class TrackSelectionStore:
    def __init__(self, max_items: int = 1000, ttl_seconds: int = 900) -> None:
        self._max_items = max_items
        self._ttl_seconds = ttl_seconds
        self._items: OrderedDict[str, tuple[float, TrackMetadata]] = OrderedDict()

    def put(self, track: TrackMetadata) -> str:
        self._prune()
        key = track.provider_track_id
        expires_at = time.time() + self._ttl_seconds
        self._items[key] = (expires_at, track)
        self._items.move_to_end(key)
        while len(self._items) > self._max_items:
            self._items.popitem(last=False)
        return key

    def get(self, track_id: str) -> TrackMetadata | None:
        self._prune()
        value = self._items.get(track_id)
        if value is None:
            return None
        expires_at, track = value
        if expires_at < time.time():
            self._items.pop(track_id, None)
            return None
        self._items.move_to_end(track_id)
        return track

    def _prune(self) -> None:
        now = time.time()
        expired = [key for key, (expires_at, _) in self._items.items() if expires_at < now]
        for key in expired:
            self._items.pop(key, None)
