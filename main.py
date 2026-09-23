import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.handlers import language, search, start
from bot.language_store import LanguageStore
from bot.providers.base import MusicSearchProvider
from bot.providers.spotify import SpotifyProvider
from config import Settings, get_settings


async def run_bot(settings: Settings) -> None:
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    search_provider: MusicSearchProvider = SpotifyProvider(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
    )
    language_store = LanguageStore()

    dispatcher.include_router(start.router)
    dispatcher.include_router(language.router)
    dispatcher.include_router(search.router)

    await dispatcher.start_polling(
        bot, search_provider=search_provider, language_store=language_store
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
