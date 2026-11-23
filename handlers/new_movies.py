import math

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database import Database
from database import movies as movies_db
from keyboards.user_kb import home_kb, new_nav_kb, select_kb
from utils.text import format_rating

router = Router(name="new_movies")
PAGE_SIZE = 5


async def _show(call: CallbackQuery, bot: Bot, db: Database, state: FSMContext, page: int) -> None:
    chat_id = call.message.chat.id
    total = await movies_db.count_movies(db)
    if total == 0:
        await bot.send_message(chat_id, "🆕 Hozircha kinolar qo‘shilmagan.", reply_markup=home_kb())
        return

    # oldingi sahifadagi xabarlarni tozalaymiz
    old_ids = (await state.get_data()).get("new_msgs", [])
    for mid in old_ids:
        try:
            await bot.delete_message(chat_id, mid)
        except TelegramAPIError:
            pass

    pages = math.ceil(total / PAGE_SIZE)
    page = max(0, min(page, pages - 1))
    sent_ids = []
    for movie in await movies_db.latest(db, PAGE_SIZE, page * PAGE_SIZE):
        caption = f"🎬 {movie['name']}\n⭐ {format_rating(movie['rating'])}"
        try:
            msg = await bot.send_photo(chat_id, movie["poster_file_id"], caption=caption, reply_markup=select_kb(movie["id"]))
        except TelegramAPIError:
            msg = await bot.send_message(chat_id, caption, reply_markup=select_kb(movie["id"]))
        sent_ids.append(msg.message_id)
    pager = await bot.send_message(chat_id, f"🆕 Yangi kinolar — {page + 1}/{pages} sahifa", reply_markup=new_nav_kb(page, pages))
    sent_ids.append(pager.message_id)
    await state.update_data(new_msgs=sent_ids)


@router.callback_query(F.data == "menu:new")
async def open_new(call: CallbackQuery, bot: Bot, db: Database, state: FSMContext) -> None:
    await call.answer()
    await state.update_data(new_msgs=[])  # bosh menyu xabarini o'chirmaslik uchun
    await _show(call, bot, db, state, 0)


@router.callback_query(F.data.startswith("new:"))
async def new_page(call: CallbackQuery, bot: Bot, db: Database, state: FSMContext) -> None:
    await call.answer()
    await _show(call, bot, db, state, int(call.data.split(":")[1]))
