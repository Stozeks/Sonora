from aiogram import F, Router
from aiogram.types import Message

router = Router()


@router.message(F.text)
async def search_handler(message: Message) -> None:
    query = (message.text or "").strip()
    if not query:
        return

    await message.answer(f"🔎 Searching for: {query}")
