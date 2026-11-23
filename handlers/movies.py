"""Kino kartochkasi, ko'rish va sevimlilarga qo'shish/o'chirish."""
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from database import Database
from database import movies as movies_db
from keyboards.user_kb import movie_kb
from services.movie_sender import send_card, send_video

router = Router(name="movies")


@router.callback_query(F.data.startswith("movie:"))
async def open_movie(call: CallbackQuery, db: Database) -> None:
    movie = await movies_db.get_by_id(db, int(call.data.split(":")[1]))
    if not movie:
        await call.answer("❌ Bu kino topilmadi (o‘chirilgan bo‘lishi mumkin).", show_alert=True)
        return
    await send_card(call.message, db, movie, call.from_user.id)
    await call.answer()


@router.callback_query(F.data.startswith("watch:"))
async def watch_movie(call: CallbackQuery, db: Database) -> None:
    movie = await movies_db.get_by_id(db, int(call.data.split(":")[1]))
    if not movie:
        await call.answer("❌ Bu kino topilmadi (o‘chirilgan bo‘lishi mumkin).", show_alert=True)
        return
    await call.answer()
    await send_video(call.message, db, movie, call.from_user.id)


@router.callback_query(F.data.startswith("fav:t:"))
async def toggle_favorite(call: CallbackQuery, db: Database) -> None:
    _, _, movie_id, show_watch = call.data.split(":")
    movie_id, show_watch = int(movie_id), bool(int(show_watch))
    if not await movies_db.get_by_id(db, movie_id):
        await call.answer("❌ Bu kino topilmadi (o‘chirilgan bo‘lishi mumkin).", show_alert=True)
        return
    user_id = call.from_user.id
    if await movies_db.is_favorite(db, user_id, movie_id):
        await movies_db.remove_favorite(db, user_id, movie_id)
        is_fav, toast = False, "💔 Sevimlilardan o‘chirildi"
    else:
        await movies_db.add_favorite(db, user_id, movie_id)
        is_fav, toast = True, "❤️ Sevimlilarga qo‘shildi"
    try:
        await call.message.edit_reply_markup(reply_markup=movie_kb(movie_id, is_fav, show_watch))
    except TelegramBadRequest:
        pass
    await call.answer(toast)
