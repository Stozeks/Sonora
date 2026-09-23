from __future__ import annotations

import base64
import re
from typing import Any

from aiohttp import ClientError, ClientSession

from bot.providers.base import MusicSearchProvider, SearchQuery, TrackMetadata

class SpotifyProviderError(Exception):
    pass


class SpotifyProvider(MusicSearchProvider):
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    SEARCH_URL = "https://api.spotify.com/v1/search"

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    async def search(self, query: SearchQuery) -> list[TrackMetadata]:
        token = await self._get_access_token()
        params = {"q": query.text, "type": "track", "limit": "10"}
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with ClientSession() as session:
                async with session.get(
                    self.SEARCH_URL, params=params, headers=headers, timeout=15
                ) as response:
                    if response.status != 200:
                        raise SpotifyProviderError("Spotify search request failed.")
                    payload = await response.json()
        except (ClientError, TimeoutError) as exc:
            raise SpotifyProviderError("Spotify search request failed.") from exc

        items = payload.get("tracks", {}).get("items", [])
        tracks = [self._parse_track(item) for item in items]
        return self._rank_and_filter(query.text, tracks)

    async def _get_access_token(self) -> str:
        basic = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode("utf-8")
        ).decode("ascii")
        headers = {"Authorization": f"Basic {basic}"}
        data = {"grant_type": "client_credentials"}

        try:
            async with ClientSession() as session:
                async with session.post(
                    self.TOKEN_URL, data=data, headers=headers, timeout=15
                ) as response:
                    if response.status != 200:
                        raise SpotifyProviderError("Spotify authorization failed.")
                    payload = await response.json()
        except (ClientError, TimeoutError) as exc:
            raise SpotifyProviderError("Spotify authorization failed.") from exc

        token = payload.get("access_token")
        if not token:
            raise SpotifyProviderError("Spotify authorization failed.")
        return token

    @staticmethod
    def _parse_track(item: dict[str, Any]) -> TrackMetadata:
        artists = item.get("artists", [])
        artist_name = artists[0].get("name") if artists else "Unknown artist"

        album = item.get("album", {})
        images = album.get("images", [])
        cover = images[0].get("url") if images else None
        release_date = album.get("release_date", "")
        release_year = release_date[:4] if release_date else "N/A"
        duration_ms = int(item.get("duration_ms", 0))

        return TrackMetadata(
            provider_track_id=str(item.get("id", "")),
            title=str(item.get("name", "Unknown title")),
            artist=str(artist_name),
            album=str(album.get("name", "Unknown album")),
            release_year=release_year,
            duration_seconds=max(duration_ms // 1000, 0),
            cover_image_url=cover,
            external_url=str(item.get("external_urls", {}).get("spotify", "")),
        )

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.casefold()
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        normalized = cls._normalize(text)
        return [token for token in normalized.split(" ") if token]

    @classmethod
    def _is_artist_like_query(cls, query_tokens: list[str], track_tokens: list[str]) -> bool:
        if len(query_tokens) < 2:
            return False
        return all(token not in track_tokens for token in query_tokens)

    @classmethod
    def _score_track(cls, query_text: str, track: TrackMetadata) -> int:
        query_norm = cls._normalize(query_text)
        query_tokens = cls._tokenize(query_text)

        title_norm = cls._normalize(track.title)
        artist_norm = cls._normalize(track.artist)
        combined_norm = f"{title_norm} {artist_norm}".strip()
        title_tokens = cls._tokenize(track.title)
        artist_tokens = cls._tokenize(track.artist)
        combined_tokens = set(title_tokens + artist_tokens)

        score = 0

        if query_norm == combined_norm:
            score += 140
        if query_norm == title_norm:
            score += 110
        if query_norm == artist_norm:
            score += 95

        if query_norm and query_norm in title_norm:
            score += 45
        if query_norm and query_norm in artist_norm:
            score += 35

        overlap = len(set(query_tokens) & combined_tokens)
        score += overlap * 12

        if query_tokens and all(token in combined_tokens for token in query_tokens):
            score += 25
        if query_tokens and all(token in artist_tokens for token in query_tokens):
            score += 30
        if query_tokens and all(token in title_tokens for token in query_tokens):
            score += 22

        if cls._is_artist_like_query(query_tokens, title_tokens):
            artist_overlap = len(set(query_tokens) & set(artist_tokens))
            score += artist_overlap * 18

        return score

    @classmethod
    def _rank_and_filter(
        cls, query_text: str, tracks: list[TrackMetadata]
    ) -> list[TrackMetadata]:
        if not tracks:
            return []

        query_tokens = cls._tokenize(query_text)
        query_norm = cls._normalize(query_text)
        has_title_artist_intent = len(query_tokens) >= 2 and " " in query_norm

        scored: list[tuple[int, TrackMetadata]] = [
            (cls._score_track(query_text, track), track) for track in tracks
        ]
        scored.sort(key=lambda item: item[0], reverse=True)

        deduped_scored: list[tuple[int, TrackMetadata]] = []
        seen_keys: set[tuple[str, str]] = set()
        for score, track in scored:
            key = (cls._normalize(track.title), cls._normalize(track.artist))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped_scored.append((score, track))

        if not deduped_scored:
            return []

        top_score = deduped_scored[0][0]
        threshold_ratio = 0.35
        if has_title_artist_intent:
            threshold_ratio = 0.48
        threshold = max(24, int(top_score * threshold_ratio))

        filtered = [track for score, track in deduped_scored if score >= threshold]
        return filtered[:5]
