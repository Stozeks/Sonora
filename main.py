import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault

from bot.handlers import language, search, start
from bot.language_store import LanguageStore
from bot.selection_store import TrackSelectionStore
from bot.providers.audio import AudioProvider, FreeToUseAudioProvider
from bot.providers.base import MusicSearchProvider
from bot.providers.spotify import SpotifyProvider
from bot.localization import tr
from config import Settings, get_settings


async def _set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description=tr("en", "command_start")),
            BotCommand(command="help", description=tr("en", "command_help")),
            BotCommand(command="language", description=tr("en", "command_language")),
        ],
        scope=BotCommandScopeDefault(),
    )
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description=tr("ru", "command_start")),
            BotCommand(command="help", description=tr("ru", "command_help")),
            BotCommand(command="language", description=tr("ru", "command_language")),
        ],
        scope=BotCommandScopeDefault(),
        language_code="ru",
    )


async def run_bot(settings: Settings) -> None:
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    search_provider: MusicSearchProvider = SpotifyProvider(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
    )
    audio_provider: AudioProvider = FreeToUseAudioProvider()
    language_store = LanguageStore()
    selection_store = TrackSelectionStore()

    dispatcher.include_router(start.router)
    dispatcher.include_router(language.router)
    dispatcher.include_router(search.router)

    await _set_bot_commands(bot)

    await dispatcher.start_polling(
        bot,
        search_provider=search_provider,
        audio_provider=audio_provider,
        language_store=language_store,
        selection_store=selection_store,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    settings = get_settings()
    asyncio.run(run_bot(settings))


if __name__ == "__main__":
    main()
