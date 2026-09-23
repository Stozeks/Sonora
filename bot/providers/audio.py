from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

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


def _build_filename(artist: str, title: str) -> str:
    raw_name = f"{artist} - {title}".strip()
    clean_name = re.sub(r'[\\/:*?"<>|]+', "", raw_name)
    clean_name = re.sub(r"\s+", " ", clean_name).strip()
    if not clean_name:
        clean_name = "track"
    return f"{clean_name}.mp3"
