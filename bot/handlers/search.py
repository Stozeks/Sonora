from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Message

from bot.language_store import LanguageStore
from bot.localization import search_labels, tr
from bot.providers.base import MusicSearchProvider, SearchQuery, TrackMetadata
from bot.providers.spotify import SpotifyProviderError

router = Router()


class TrackSelectCallback(CallbackData, prefix="trk"):
    provider: str
    track_id: str


def _duration_to_text(duration_seconds: int) -> str:
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    return f"{minutes}:{seconds:02d}"


def _build_result_text(track: TrackMetadata, index: int, language: str) -> str:
    duration = _duration_to_text(track.duration_seconds)
    labels = search_labels(language)
    return (
        f"{index}. <b>{track.title}</b> — {track.artist}\n"
        f"{labels.album}: {track.album}\n"
        f"{labels.year}: {track.release_year}\n"
        f"{labels.duration}: {duration}"
    )


def _build_results_keyboard(tracks: list[TrackMetadata]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{i}. {track.title} — {track.artist}",
                callback_data=TrackSelectCallback(
                    provider="spotify", track_id=track.provider_track_id
                ).pack(),
            )
        ]
        for i, track in enumerate(tracks, start=1)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text)
async def search_handler(
    message: Message,
    search_provider: MusicSearchProvider,
    language_store: LanguageStore,
) -> None:
    query = (message.text or "").strip()
    if not query:
        return
    user = message.from_user
    if user is None:
        return
    language = language_store.resolve(user.id, user.language_code)

    await message.answer(tr(language, "searching", query=query))

    try:
        tracks = await search_provider.search(SearchQuery(text=query))
    except SpotifyProviderError:
        await message.answer(tr(language, "search_error"))
        return

    if not tracks:
        await message.answer(tr(language, "no_results"))
        return

    text = "\n\n".join(
        _build_result_text(track=track, index=index, language=language)
        for index, track in enumerate(tracks, start=1)
    )
    keyboard = _build_results_keyboard(tracks)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
