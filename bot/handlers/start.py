from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.language_store import LanguageStore
from bot.localization import tr

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, language_store: LanguageStore) -> None:
    user = message.from_user
    if user is None:
        return
    language = language_store.resolve(user.id, user.language_code)
    await message.answer(tr(language, "start"))
