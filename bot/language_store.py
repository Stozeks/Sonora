from __future__ import annotations

import json
from pathlib import Path

from bot.localization import normalize_language


class LanguageStore:
    def __init__(self, path: str = "data/user_languages.json") -> None:
        self._path = Path(path)
        self._cache: dict[str, str] = {}
        self._loaded = False

    def get(self, user_id: int) -> str | None:
        self._ensure_loaded()
        return self._cache.get(str(user_id))

    def set(self, user_id: int, language: str) -> None:
        self._ensure_loaded()
        self._cache[str(user_id)] = normalize_language(language)
        self._persist()

    def resolve(self, user_id: int, telegram_language_code: str | None) -> str:
        stored = self.get(user_id)
        if stored:
            return stored
        return normalize_language(telegram_language_code)

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._cache = {
                        str(k): normalize_language(str(v)) for k, v in data.items()
                    }
            except (json.JSONDecodeError, OSError):
                self._cache = {}
        self._loaded = True

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
