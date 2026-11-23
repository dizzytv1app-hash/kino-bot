import math

from aiogram import F, Router
from aiogram.types import CallbackQuery

from database import Database
from database import movies as movies_db
from keyboards.user_kb import home_kb, movies_kb
from utils.tg import safe_edit

router = Router(name="favorites")
PAGE_SIZE = 8


async def _render(call: CallbackQuery, db: Database, page: int, edit: bool) -> None:
    user_id = call.from_user.id
    total = await movies_db.count_favorites(db, user_id)
    if total == 0:
        text, kb = "❤️ Sevimlilar ro‘yxati hozircha bo‘sh.\n\nKino kartochkasidagi “❤️ Sevimlilarga qo‘shish” tugmasi orqali qo‘shing.", home_kb()
        if edit:
            await safe_edit(call, text, kb)
        else:
            await call.message.answer(text, reply_markup=kb)
        return
    pages = math.ceil(total / PAGE_SIZE)
    page = max(0, min(page, pages - 1))
    items = await movies_db.favorites_page(db, user_id, PAGE_SIZE, page * PAGE_SIZE)
    text = f"❤️ Sevimlilaringiz: {total} ta"
    kb = movies_kb(items, page, pages, "fav:l")
    if edit:
        await safe_edit(call, text, kb)
    else:
        await call.message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "menu:favorites")
async def open_favorites(call: CallbackQuery, db: Database) -> None:
    await _render(call, db, 0, edit=False)
    await call.answer()


@router.callback_query(F.data.startswith("fav:l:"))
async def favorites_page(call: CallbackQuery, db: Database) -> None:
    await _render(call, db, int(call.data.split(":")[2]), edit=True)
    await call.answer()
