from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "🎵 Sonora\n\n"
        "Send me a track name or artist + track name and I'll find the music for you."
    )
