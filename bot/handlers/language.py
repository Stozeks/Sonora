from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.language_store import LanguageStore
from bot.localization import tr

router = Router()


class LanguageCallback(CallbackData, prefix="lang"):
    code: str


def _language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский",
                    callback_data=LanguageCallback(code="ru").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇬🇧 English",
                    callback_data=LanguageCallback(code="en").pack(),
                )
            ],
        ]
    )


@router.message(Command("language"))
async def language_command(
    message: Message, language_store: LanguageStore
) -> None:
    user = message.from_user
    if user is None:
        return
    language = language_store.resolve(user.id, user.language_code)
    await message.answer(tr(language, "language_title"), reply_markup=_language_keyboard())


@router.callback_query(LanguageCallback.filter())
async def language_select(
    callback: CallbackQuery, callback_data: LanguageCallback, language_store: LanguageStore
) -> None:
    user = callback.from_user
    language_store.set(user.id, callback_data.code)
    await callback.answer()
    await callback.message.answer(tr(callback_data.code, "language_saved"))
