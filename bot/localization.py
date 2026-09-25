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
        "searching": "🔎 Looking for: {query}",
        "search_error": "Search is unavailable right now. Please try again.",
        "no_results": "Nothing found. Try another query.",
        "track_selected": "🎵 {title} — {artist}\n\nPreparing audio...",
        "audio_caption": '<a href="https://t.me/MusicForYourMood_sacrament">🎧 Music, stories & moods for every taste</a>',
        "audio_unavailable": "This track is unavailable right now.",
        "selection_expired": "This selection has expired. Search again.",
        "selection_invalid": "This selection is no longer valid. Search again.",
        "language_title": "Choose your language:",
        "language_saved": "Language changed to English.",
        "labels": SearchLabels(album="Album", year="Year", duration="Duration"),
    },
    "ru": {
        "start": "🎵 Sonora\n\nОтправь название трека или артист + трек, и я найду музыку.",
        "searching": "🔎 Ищу: {query}",
        "search_error": "Сейчас поиск недоступен. Попробуйте ещё раз.",
        "no_results": "Ничего не нашлось. Попробуйте другой запрос.",
        "track_selected": "🎵 {title} — {artist}\n\nПодготавливаю аудио...",
        "audio_caption": '<a href="https://t.me/MusicForYourMood_sacrament">🎧 Музыка, истории и настроение — на любой вкус</a>',
        "audio_unavailable": "Сейчас этот трек недоступен.",
        "selection_expired": "Этот выбор уже устарел. Выполните поиск снова.",
        "selection_invalid": "Этот выбор больше недоступен. Найдите трек снова.",
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
