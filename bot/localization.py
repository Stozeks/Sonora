from __future__ import annotations

from dataclasses import dataclass


DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"en", "ru"}


@dataclass(frozen=True)
class SearchLabels:
    album: str
    year: str
    duration: str


_TEXTS = {
    "en": {
        "start": "🎵 Sonora\n\nSend me a track name or artist + track name and I'll find the music for you.",
        "searching": "🔎 Searching for: {query}",
        "search_error": "Search is temporarily unavailable. Please try again.",
        "no_results": "No tracks found. Try another query.",
        "language_title": "Choose your language:",
        "language_saved": "Language changed to English.",
        "labels": SearchLabels(album="Album", year="Year", duration="Duration"),
    },
    "ru": {
        "start": "🎵 Sonora\n\nОтправь название трека или артист + трек, и я найду музыку.",
        "searching": "🔎 Ищу: {query}",
        "search_error": "Поиск временно недоступен. Попробуйте снова.",
        "no_results": "Ничего не найдено. Попробуйте другой запрос.",
        "language_title": "Выберите язык:",
        "language_saved": "Язык переключен на русский.",
        "labels": SearchLabels(album="Альбом", year="Год", duration="Длительность"),
    },
}


def normalize_language(language_code: str | None) -> str:
    if not language_code:
        return DEFAULT_LANGUAGE
    code = language_code.lower()
    if code.startswith("ru"):
        return "ru"
    return DEFAULT_LANGUAGE


def tr(language: str, key: str, **kwargs: str) -> str:
    lang = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    value = _TEXTS[lang][key]
    if isinstance(value, SearchLabels):
        raise TypeError("Use search_labels() for labels.")
    if kwargs:
        return value.format(**kwargs)
    return value


def search_labels(language: str) -> SearchLabels:
    lang = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    labels = _TEXTS[lang]["labels"]
    if isinstance(labels, SearchLabels):
        return labels
    raise TypeError("Invalid label configuration.")
