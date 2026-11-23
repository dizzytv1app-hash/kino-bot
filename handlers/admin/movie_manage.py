"""Kinoni tahrirlash, o'chirish va kinolar ro'yxati."""
import math

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import Database
from database import movies as movies_db
from keyboards.admin_kb import (FIELD_LABELS, back_kb, cancel_kb, confirm_delete_kb,
                                fields_kb, pager_kb)
from states.admin import DeleteMovie, EditMovie
from utils.filters import make_admin_router
from utils.tg import safe_edit
from utils.text import format_rating, movie_caption, parse_rating, valid_code

router = make_admin_router("admin_movie_manage")
LIST_PAGE = 15

DB_FIELD = {"code": "code", "name": "name", "poster": "poster_file_id", "video": "video_file_id", "rating": "rating"}
EDIT_PROMPTS = {
    "code": "Yangi kino kodini kiriting:",
    "name": "Yangi kino nomini kiriting:",
    "poster": "Yangi posterni (rasm) yuboring:",
    "video": "Yangi videoni yuboring:",
    "rating": "Yangi reytingni kiriting (0–10):",
}


async def _send_movie_card(message: Message, movie: dict, kb, extra: str = "") -> None:
    caption = movie_caption(movie) + extra
    await message.answer_photo(movie["poster_file_id"], caption=caption, reply_markup=kb)


# ===================== TAHRIRLASH =====================
@router.callback_query(F.data == "adm:movie_edit")
async def edit_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(EditMovie.code)
    await call.message.answer("✏️ Tahrirlanadigan kino kodini kiriting:", reply_markup=cancel_kb())
    await call.answer()


@router.message(EditMovie.code, F.text)
async def edit_got_code(message: Message, state: FSMContext, db: Database) -> None:
    movie = await movies_db.get_by_code(db, message.text.strip())
    if not movie:
        await message.answer("❌ Bunday kodli kino topilmadi. Qayta kiriting:", reply_markup=cancel_kb())
        return
    await state.update_data(movie_id=movie["id"])
    await state.set_state(EditMovie.choose)
    await _send_movie_card(message, movie, fields_kb("adm:ef", "adm:home", "✅ Tugatish"), "\n\nQaysi ma'lumotni o‘zgartirasiz?")


@router.callback_query(EditMovie.choose, F.data.startswith("adm:ef:"))
async def edit_choose_field(call: CallbackQuery, state: FSMContext) -> None:
    field = call.data.split(":")[2]
    if field not in FIELD_LABELS:
        await call.answer()
        return
    await state.update_data(field=field)
    await state.set_state(EditMovie.value)
    await call.message.answer(EDIT_PROMPTS[field], reply_markup=cancel_kb())
    await call.answer()


@router.message(EditMovie.value)
async def edit_got_value(message: Message, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    field, movie_id = data["field"], data["movie_id"]

    if field in ("code", "name", "rating"):
        if not message.text:
            await message.answer("❗ Iltimos, matn yuboring.", reply_markup=cancel_kb())
            return
        text = message.text.strip()
        if field == "code":
            if not valid_code(text):
                await message.answer("❗ Kod faqat lotin harf/raqam/“-”/“_” dan iborat, 1–20 belgi. Qayta kiriting:", reply_markup=cancel_kb())
                return
            if await movies_db.code_taken(db, text, exclude_id=movie_id):
                await message.answer("❗ Bu kod boshqa kinoda mavjud. Boshqa kod kiriting:", reply_markup=cancel_kb())
                return
            value = text
        elif field == "name":
            if not 1 <= len(text) <= 200:
                await message.answer("❗ Nom 1–200 belgi bo‘lishi kerak. Qayta kiriting:", reply_markup=cancel_kb())
                return
            value = text
        else:
            value = parse_rating(text)
            if value is None:
                await message.answer("❗ Reyting 0 dan 10 gacha son bo‘lishi kerak. Qayta kiriting:", reply_markup=cancel_kb())
                return
    elif field == "poster":
        if not message.photo:
            await message.answer("❗ Iltimos, rasm yuboring.", reply_markup=cancel_kb())
            return
        value = message.photo[-1].file_id
    else:  # video
        if not message.video:
            await message.answer("❗ Iltimos, video yuboring (fayl emas, video ko‘rinishida).", reply_markup=cancel_kb())
            return
        value = message.video.file_id

    await movies_db.update_field(db, movie_id, DB_FIELD[field], value)
    movie = await movies_db.get_by_id(db, movie_id)
    await state.set_state(EditMovie.choose)
    await _send_movie_card(message, movie, fields_kb("adm:ef", "adm:home", "✅ Tugatish"),
                           "\n\n✅ Saqlandi. Yana o‘zgartirasizmi?")


# ===================== O'CHIRISH =====================
@router.callback_query(F.data == "adm:movie_delete")
async def delete_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(DeleteMovie.code)
    await call.message.answer("🗑 O‘chiriladigan kino kodini kiriting:", reply_markup=cancel_kb())
    await call.answer()


@router.message(DeleteMovie.code, F.text)
async def delete_got_code(message: Message, state: FSMContext, db: Database) -> None:
    movie = await movies_db.get_by_code(db, message.text.strip())
    if not movie:
        await message.answer("❌ Bunday kodli kino topilmadi. Qayta kiriting:", reply_markup=cancel_kb())
        return
    await state.update_data(movie_id=movie["id"])
    await state.set_state(DeleteMovie.confirm)
    await _send_movie_card(message, movie, confirm_delete_kb(), "\n\n❓ Rostdan ham o‘chirasizmi? Bu amalni qaytarib bo‘lmaydi.")


@router.callback_query(DeleteMovie.confirm, F.data == "adm:del_yes")
async def delete_confirm(call: CallbackQuery, state: FSMContext, db: Database) -> None:
    movie_id = (await state.get_data())["movie_id"]
    await movies_db.delete_movie(db, movie_id)
    await state.clear()
    await call.message.answer("✅ Kino o‘chirildi.", reply_markup=back_kb())
    await call.answer()


# ===================== RO'YXAT =====================
async def _list(call: CallbackQuery, db: Database, page: int) -> None:
    total = await movies_db.count_movies(db)
    if total == 0:
        await safe_edit(call, "📋 Hozircha kinolar yo‘q.", back_kb())
        return
    pages = math.ceil(total / LIST_PAGE)
    page = max(0, min(page, pages - 1))
    items = await movies_db.latest(db, LIST_PAGE, page * LIST_PAGE)
    lines = [f"{page * LIST_PAGE + i}. 🔢 {m['code']} — {m['name']} (⭐ {format_rating(m['rating'])})"
             for i, m in enumerate(items, 1)]
    text = f"📋 Kinolar ro‘yxati (jami: {total})\n\n" + "\n".join(lines)
    await safe_edit(call, text, pager_kb(page, pages, "adm:ml"))


@router.callback_query(F.data == "adm:movie_list")
async def list_first(call: CallbackQuery, db: Database) -> None:
    await _list(call, db, 0)
    await call.answer()


@router.callback_query(F.data.startswith("adm:ml:"))
async def list_page(call: CallbackQuery, db: Database) -> None:
    await _list(call, db, int(call.data.split(":")[2]))
    await call.answer()
