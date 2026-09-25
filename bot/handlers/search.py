import logging
from contextlib import suppress

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.types import Message

from bot.language_store import LanguageStore
from bot.localization import search_labels, tr
from bot.selection_store import TrackSelectionStore
from bot.providers.audio import AudioProvider, AudioProviderError
from bot.providers.base import MusicSearchProvider, SearchQuery, TrackMetadata
from bot.providers.spotify import SpotifyProviderError

router = Router()
logger = logging.getLogger(__name__)


class TrackSelectCallback(CallbackData, prefix="trk"):
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


def _build_results_keyboard(
    tracks: list[TrackMetadata], selection_store: TrackSelectionStore
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{i}. {track.title} — {track.artist}",
                callback_data=TrackSelectCallback(
                    track_id=selection_store.put(track)
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
    selection_store: TrackSelectionStore,
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
    keyboard = _build_results_keyboard(tracks, selection_store)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(TrackSelectCallback.filter())
async def track_selected_handler(
    callback: CallbackQuery,
    callback_data: TrackSelectCallback,
    language_store: LanguageStore,
    selection_store: TrackSelectionStore,
    audio_provider: AudioProvider,
) -> None:
    user = callback.from_user
    language = language_store.resolve(user.id, user.language_code)
    await callback.answer()

    track = selection_store.get(callback_data.track_id)
    if track is None:
        await callback.message.answer(tr(language, "selection_expired"))
        return

    await callback.message.answer(
        tr(language, "track_selected", title=track.title, artist=track.artist)
    )

    try:
        payload = await audio_provider.resolve_audio(track)
    except AudioProviderError:
        logger.warning("Audio provider could not resolve audio for track %s", track.provider_track_id)
        await callback.message.answer(tr(language, "audio_unavailable"))
        return
    except Exception:
        logger.exception("Unexpected audio provider error")
        await callback.message.answer(tr(language, "audio_unavailable"))
        return

    thumbnail = None
    if payload.thumbnail_url:
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(payload.thumbnail_url, timeout=8) as response:
                    if response.status == 200:
                        data = await response.read()
                        if data:
                            thumbnail = BufferedInputFile(data, filename="thumb.jpg")
        except Exception:
            thumbnail = None

    try:
        try:
            await callback.message.answer_audio(
                audio=FSInputFile(path=payload.file_path, filename=payload.filename),
                title=payload.title,
                performer=payload.performer,
                duration=payload.duration_seconds,
                caption=tr(language, "audio_caption"),
                parse_mode="HTML",
                thumbnail=thumbnail,
            )
        except Exception:
            logger.exception("Failed to send audio for track %s", track.provider_track_id)
            await callback.message.answer(tr(language, "audio_unavailable"))
    finally:
        if payload.temporary:
            with suppress(OSError):
                payload.file_path.unlink()
