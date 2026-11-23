"""Kino kartochkasi va videosini yuborish."""
import logging

from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from database import Database
from database import movies as movies_db
from keyboards.user_kb import home_kb, movie_kb
from utils.text import movie_caption

log = logging.getLogger(__name__)


async def send_card(message: Message, db: Database, movie: dict, user_id: int) -> None:
    """Poster + nom + reyting + 'Ko'rish' tugmasi."""
    fav = await movies_db.is_favorite(db, user_id, movie["id"])
    try:
        await message.answer_photo(
            movie["poster_file_id"],
            caption=movie_caption(movie),
            reply_markup=movie_kb(movie["id"], fav, show_watch=True),
        )
    except TelegramAPIError:
        log.exception("Posterni yuborib bo'lmadi (movie_id=%s)", movie["id"])
        await message.answer(movie_caption(movie), reply_markup=movie_kb(movie["id"], fav, True))


async def send_video(message: Message, db: Database, movie: dict, user_id: int) -> None:
    fav = await movies_db.is_favorite(db, user_id, movie["id"])
    try:
        await message.answer_video(
            movie["video_file_id"],
            caption=movie_caption(movie),
            reply_markup=movie_kb(movie["id"], fav, show_watch=False),
        )
    except TelegramAPIError:
        log.exception("Videoni yuborib bo'lmadi (movie_id=%s)", movie["id"])
        await message.answer("⚠️ Videoni yuborib bo‘lmadi. Iltimos, keyinroq urinib ko‘ring.", reply_markup=home_kb())
        return
    await movies_db.add_view(db, user_id, movie["id"])
