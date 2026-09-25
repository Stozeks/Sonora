from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from bot.providers.base import TrackMetadata


@dataclass(frozen=True)
class AudioPayload:
    file_path: Path
    filename: str
    title: str
    performer: str
    duration_seconds: int | None = None
    thumbnail_url: str | None = None


class AudioProvider(ABC):
    @abstractmethod
    async def resolve_audio(self, track: TrackMetadata) -> AudioPayload:
        ...


class AudioProviderError(Exception):
    pass


class DevelopmentAudioProvider(AudioProvider):
    def __init__(self, relative_test_file: str = "test_audio.mp3") -> None:
        self._relative_test_file = relative_test_file

    async def resolve_audio(self, track: TrackMetadata) -> AudioPayload:
        project_root = Path(__file__).resolve().parents[2]
        file_path = project_root / self._relative_test_file
        if not file_path.exists() or not file_path.is_file():
            raise AudioProviderError("Development audio file is unavailable.")

        return AudioPayload(
            file_path=file_path,
            filename=_build_filename(track.artist, track.title),
            title=track.title,
            performer=track.artist,
            duration_seconds=track.duration_seconds,
            thumbnail_url=track.cover_image_url,
        )


class FreeToUseAudioProvider(AudioProvider):
    SEARCH_URL = "https://api.freetouse.com/v3/music/tracks/search"
    SEARCH_TIMEOUT = ClientTimeout(total=12, connect=4, sock_read=8)
    DOWNLOAD_TIMEOUT = ClientTimeout(total=30, connect=6, sock_read=20)
    MIN_MATCH_SCORE = 0.76
    MAX_DURATION_DELTA_SECONDS = 12

    async def resolve_audio(self, track: TrackMetadata) -> AudioPayload:
        candidate = await self._find_candidate(track)
        if candidate is None:
            raise AudioProviderError("Audio is unavailable for this track.")

        audio_url = self._extract_audio_url(candidate)
        if not audio_url:
            raise AudioProviderError("Audio file is unavailable for this track.")

        file_path = await self._download_audio(audio_url)
        thumbnail_url = self._extract_thumbnail_url(candidate) or track.cover_image_url

        return AudioPayload(
            file_path=file_path,
            filename=_build_filename(track.artist, track.title),
            title=track.title,
            performer=track.artist,
            duration_seconds=track.duration_seconds,
            thumbnail_url=thumbnail_url,
        )

    async def _find_candidate(self, track: TrackMetadata) -> dict[str, Any] | None:
        params = {"query": f"{track.artist} {track.title}"}

        try:
            async with ClientSession(timeout=self.SEARCH_TIMEOUT) as session:
                async with session.get(self.SEARCH_URL, params=params) as response:
                    if response.status != 200:
                        raise AudioProviderError("FreeToUse search request failed.")
                    payload = await response.json()
        except (ClientError, TimeoutError, ValueError) as exc:
            raise AudioProviderError("FreeToUse search request failed.") from exc

        items = self._extract_items(payload)
        if not items:
            return None

        best_match: dict[str, Any] | None = None
        best_score = 0.0

        for item in items:
            score = self._score_match(track, item)
            if score > best_score:
                best_score = score
                best_match = item

        if best_score < self.MIN_MATCH_SCORE:
            return None
        return best_match

    @staticmethod
    def _extract_items(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ("data", "tracks", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    @classmethod
    def _score_match(cls, track: TrackMetadata, item: dict[str, Any]) -> float:
        item_title = str(item.get("title") or "")
        artist_names = cls._extract_artist_names(item)
        if not item_title or not artist_names:
            return 0.0

        title_score = cls._similarity(track.title, item_title)
        artist_score = max(
            (cls._similarity(track.artist, artist_name) for artist_name in artist_names),
            default=0.0,
        )
        duration_score = cls._duration_score(
            track.duration_seconds, cls._extract_duration_seconds(item)
        )

        if title_score < 0.72 or artist_score < 0.72:
            return 0.0

        return (title_score * 0.55) + (artist_score * 0.35) + (duration_score * 0.10)

    @staticmethod
    def _extract_artist_names(item: dict[str, Any]) -> list[str]:
        artists = item.get("artists")
        if not isinstance(artists, (list, tuple)):
            return []

        names: list[str] = []

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                name = value.get("name")
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
                return
            if isinstance(value, (list, tuple)):
                for nested in value:
                    walk(nested)

        walk(artists)
        return names

    @staticmethod
    def _extract_duration_seconds(item: dict[str, Any]) -> int | None:
        value = item.get("duration")
        if isinstance(value, (int, float)):
            seconds = int(value)
            return seconds if seconds >= 0 else None
        if isinstance(value, str) and value.isdigit():
            seconds = int(value)
            return seconds if seconds >= 0 else None
        return None

    @classmethod
    def _duration_score(
        cls, expected_duration: int, actual_duration: int | None
    ) -> float:
        if actual_duration is None or expected_duration <= 0:
            return 0.5
        delta = abs(expected_duration - actual_duration)
        if delta > cls.MAX_DURATION_DELTA_SECONDS:
            return 0.0
        return max(0.0, 1 - (delta / cls.MAX_DURATION_DELTA_SECONDS))

    @classmethod
    def _similarity(cls, left: str, right: str) -> float:
        left_norm = cls._normalize_for_match(left)
        right_norm = cls._normalize_for_match(right)
        if not left_norm or not right_norm:
            return 0.0
        if left_norm == right_norm:
            return 1.0
        left_tokens = cls._tokenize_for_match(left_norm)
        right_tokens = cls._tokenize_for_match(right_norm)
        if not left_tokens or not right_tokens:
            return 0.0

        overlap = len(left_tokens & right_tokens)
        token_score = (2 * overlap) / (len(left_tokens) + len(right_tokens))
        contains_score = 1.0 if left_norm in right_norm or right_norm in left_norm else 0.0
        return max(token_score, contains_score * 0.92)

    @staticmethod
    def _normalize_for_match(text: str) -> str:
        normalized = text.casefold()
        normalized = re.sub(r"\((feat|ft|with)[^)]*\)", " ", normalized)
        normalized = re.sub(r"\[(feat|ft|with)[^\]]*\]", " ", normalized)
        normalized = re.sub(r"\b(feat|ft|with|x)\b", " ", normalized)
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    @classmethod
    def _tokenize_for_match(cls, text: str) -> set[str]:
        return {token for token in text.split(" ") if token}

    @staticmethod
    def _extract_audio_url(item: dict[str, Any]) -> str | None:
        files = item.get("files")
        if not isinstance(files, dict):
            return None
        audio_url = files.get("mp3")
        if isinstance(audio_url, str) and audio_url.strip():
            return audio_url.strip()
        return None

    @staticmethod
    def _extract_thumbnail_url(item: dict[str, Any]) -> str | None:
        thumbnails = item.get("thumbnails")
        if isinstance(thumbnails, list):
            for thumbnail in thumbnails:
                if not isinstance(thumbnail, dict):
                    continue
                url = thumbnail.get("url")
                if isinstance(url, str) and url.strip():
                    return url.strip()
        elif isinstance(thumbnails, dict):
            for key in ("xl", "lg", "md", "sm", "url"):
                url = thumbnails.get(key)
                if isinstance(url, str) and url.strip():
                    return url.strip()
        return None

    async def _download_audio(self, audio_url: str) -> Path:
        try:
            async with ClientSession(timeout=self.DOWNLOAD_TIMEOUT) as session:
                async with session.get(audio_url) as response:
                    if response.status != 200:
                        raise AudioProviderError("FreeToUse audio download failed.")
                    data = await response.read()
        except (ClientError, TimeoutError) as exc:
            raise AudioProviderError("FreeToUse audio download failed.") from exc

        if not data:
            raise AudioProviderError("FreeToUse audio download failed.")

        with NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(data)
            return Path(tmp_file.name)


def _build_filename(artist: str, title: str) -> str:
    raw_name = f"{artist} - {title}".strip()
    clean_name = re.sub(r'[\\/:*?"<>|]+', "", raw_name)
    clean_name = re.sub(r"\s+", " ", clean_name).strip()
    if not clean_name:
        clean_name = "track"
    return f"{clean_name}.mp3"
