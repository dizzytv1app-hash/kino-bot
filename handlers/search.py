from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import Database
from database import movies as movies_db
from keyboards.user_kb import home_kb, movies_kb, search_again_kb
from states.user import SearchState
from utils.text import normalize

router = Router(name="search")
MAX_RESULTS = 10


@router.callback_query(F.data == "menu:search")
async def ask_query(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SearchState.query)
    await call.message.answer("🔎 Kino nomini yozing (to‘liq yoki qisman):", reply_markup=home_kb())
    await call.answer()


@router.message(SearchState.query, F.text)
async def do_search(message: Message, state: FSMContext, db: Database) -> None:
    query = normalize(message.text)
    if len(query) < 2:
        await message.answer("❗ Kamida 2 ta belgi kiriting.", reply_markup=home_kb())
        return
    await state.clear()
    found = await movies_db.search(db, query, MAX_RESULTS + 1)
    if not found:
        await message.answer("❌ Bunday kino topilmadi. Boshqa nom bilan urinib ko‘ring.", reply_markup=search_again_kb())
        return
    text = f"🔎 Qidiruv natijalari: “{message.text.strip()[:50]}”"
    if len(found) > MAX_RESULTS:
        text += f"\n\nEng mos {MAX_RESULTS} ta natija ko‘rsatildi. Aniqroq nom yozsangiz, natija yaxshiroq bo‘ladi."
    await message.answer(text, reply_markup=movies_kb(found[:MAX_RESULTS]))


@router.message(SearchState.query)
async def search_wrong_type(message: Message) -> None:
    await message.answer("❗ Iltimos, kino nomini matn ko‘rinishida yozing.", reply_markup=home_kb())
