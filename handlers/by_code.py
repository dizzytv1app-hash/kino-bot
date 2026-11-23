"""Foydalanuvchi kino kodini to'g'ridan-to'g'ri yuborganda video yuboradi."""
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from database import Database
from database import movies as movies_db
from keyboards.user_kb import home_kb
from services.movie_sender import send_video

router = Router(name="by_code")


@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def movie_by_code(message: Message, db: Database) -> None:
    movie = await movies_db.get_by_code(db, message.text.strip())
    if not movie:
        await message.answer("❌ Bunday kodli kino topilmadi", reply_markup=home_kb())
        return
    await send_video(message, db, movie, message.from_user.id)
