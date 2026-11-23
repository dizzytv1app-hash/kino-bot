"""Kino qo'shish: kod -> nom -> poster -> video -> reyting -> tasdiqlash."""
import logging
import sqlite3

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import Database
from database import movies as movies_db
from keyboards.admin_kb import FIELD_LABELS, back_kb, cancel_kb, confirm_add_kb, fields_kb
from states.admin import AddMovie
from utils.filters import make_admin_router
from utils.text import format_rating, parse_rating, valid_code

log = logging.getLogger(__name__)
router = make_admin_router("admin_movie_add")

ORDER = ["code", "name", "poster", "video", "rating"]
STATES = {"code": AddMovie.code, "name": AddMovie.name, "poster": AddMovie.poster,
          "video": AddMovie.video, "rating": AddMovie.rating}
PROMPTS = {
    "code": "1️⃣ Kino kodini kiriting (lotin harf/raqam, masalan 1025):",
    "name": "2️⃣ Kino nomini kiriting:",
    "poster": "3️⃣ Kino posterini (rasm) yuboring:",
    "video": "4️⃣ Kino videosini yuboring (video ko‘rinishida, fayl emas):",
    "rating": "5️⃣ Kino reytingini kiriting (0 dan 10 gacha, masalan 8.5):",
}


async def ask(message: Message, state: FSMContext, field: str) -> None:
    await state.set_state(STATES[field])
    await message.answer(PROMPTS[field], reply_markup=cancel_kb())


async def show_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(AddMovie.confirm)
    await state.update_data(from_confirm=False)
    caption = (
        "🎬 Kino ma'lumotlari\n\n"
        f"🔢 Kodi: {data['code']}\n"
        f"📝 Nomi: {data['name']}\n"
        f"⭐ Reytingi: {format_rating(data['rating'])}\n"
        "🎥 Video: ✅ mavjud"
    )
    await message.answer_photo(data["poster"], caption=caption, reply_markup=confirm_add_kb())


async def advance(message: Message, state: FSMContext, done: str) -> None:
    if (await state.get_data()).get("from_confirm"):
        await show_confirm(message, state)
        return
    idx = ORDER.index(done)
    if idx + 1 < len(ORDER):
        await ask(message, state, ORDER[idx + 1])
    else:
        await show_confirm(message, state)


@router.callback_query(F.data == "adm:movie_add")
async def start_add(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(from_confirm=False)
    await ask(call.message, state, "code")
    await call.answer()


# ---- 1. kod ----
@router.message(AddMovie.code, F.text)
async def got_code(message: Message, state: FSMContext, db: Database) -> None:
    code = message.text.strip()
    if not valid_code(code):
        await message.answer("❗ Kod faqat lotin harflari, raqamlar, “-” va “_” dan iborat bo‘lib, 1–20 belgi bo‘lishi kerak. Qayta kiriting:", reply_markup=cancel_kb())
        return
    if await movies_db.code_taken(db, code):
        await message.answer("❗ Bu kod allaqachon mavjud. Boshqa kod kiriting:", reply_markup=cancel_kb())
        return
    await state.update_data(code=code)
    await advance(message, state, "code")


# ---- 2. nom ----
@router.message(AddMovie.name, F.text)
async def got_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not 1 <= len(name) <= 200:
        await message.answer("❗ Nom 1 dan 200 gacha belgi bo‘lishi kerak. Qayta kiriting:", reply_markup=cancel_kb())
        return
    await state.update_data(name=name)
    await advance(message, state, "name")


# ---- 3. poster ----
@router.message(AddMovie.poster, F.photo)
async def got_poster(message: Message, state: FSMContext) -> None:
    await state.update_data(poster=message.photo[-1].file_id)
    await advance(message, state, "poster")


# ---- 4. video ----
@router.message(AddMovie.video, F.video)
async def got_video(message: Message, state: FSMContext) -> None:
    await state.update_data(video=message.video.file_id)
    await advance(message, state, "video")


# ---- 5. reyting ----
@router.message(AddMovie.rating, F.text)
async def got_rating(message: Message, state: FSMContext) -> None:
    rating = parse_rating(message.text)
    if rating is None:
        await message.answer("❗ Reyting 0 dan 10 gacha son bo‘lishi kerak (masalan 8.5). Qayta kiriting:", reply_markup=cancel_kb())
        return
    await state.update_data(rating=rating)
    await advance(message, state, "rating")


# ---- noto'g'ri turdagi kontent ----
@router.message(AddMovie.code)
@router.message(AddMovie.name)
@router.message(AddMovie.rating)
async def wrong_text(message: Message) -> None:
    await message.answer("❗ Iltimos, matn yuboring.", reply_markup=cancel_kb())


@router.message(AddMovie.poster)
async def wrong_poster(message: Message) -> None:
    await message.answer("❗ Iltimos, poster sifatida rasm yuboring.", reply_markup=cancel_kb())


@router.message(AddMovie.video)
async def wrong_video(message: Message) -> None:
    await message.answer("❗ Iltimos, video yuboring (fayl emas, video ko‘rinishida).", reply_markup=cancel_kb())


@router.message(AddMovie.confirm)
async def confirm_text(message: Message) -> None:
    await message.answer("Yuqoridagi tugmalardan birini tanlang.")


# ---- tasdiqlash oynasi ----
@router.callback_query(AddMovie.confirm, F.data == "adm:add_save")
async def save(call: CallbackQuery, state: FSMContext, db: Database) -> None:
    d = await state.get_data()
    try:
        await movies_db.add_movie(db, d["code"], d["name"], d["poster"], d["video"], d["rating"])
    except sqlite3.IntegrityError:
        await call.answer("❌ Bu kod band bo‘lib qoldi, boshqa kod kiriting.", show_alert=True)
        await state.update_data(from_confirm=True)
        await ask(call.message, state, "code")
        return
    await state.clear()
    await call.message.answer("✅ Kino muvaffaqiyatli saqlandi!", reply_markup=back_kb())
    await call.answer()


@router.callback_query(AddMovie.confirm, F.data == "adm:add_edit")
async def edit_menu(call: CallbackQuery) -> None:
    await call.message.answer("Qaysi ma'lumotni o‘zgartirasiz?", reply_markup=fields_kb("adm:af", "adm:add_back"))
    await call.answer()


@router.callback_query(AddMovie.confirm, F.data == "adm:add_back")
async def edit_back(call: CallbackQuery, state: FSMContext) -> None:
    await show_confirm(call.message, state)
    await call.answer()


@router.callback_query(AddMovie.confirm, F.data.startswith("adm:af:"))
async def edit_field(call: CallbackQuery, state: FSMContext) -> None:
    field = call.data.split(":")[2]
    if field not in FIELD_LABELS:
        await call.answer()
        return
    await state.update_data(from_confirm=True)
    await ask(call.message, state, field)
    await call.answer()
