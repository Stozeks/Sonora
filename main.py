import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.handlers import search, start
from config import Settings, get_settings


async def run_bot(settings: Settings) -> None:
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()

    dispatcher.include_router(start.router)
    dispatcher.include_router(search.router)

    await dispatcher.start_polling(bot)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    settings = get_settings()
    asyncio.run(run_bot(settings))


if __name__ == "__main__":
    main()
