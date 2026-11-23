from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database import Database
from handlers.common import WELCOME_TEXT
from keyboards.user_kb import channel_kb, main_menu_kb

router = Router(name="menu")


@router.callback_query(F.data == "menu:home")
async def menu_home(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())
    await call.answer()


@router.callback_query(F.data == "menu:channel")
async def menu_channel(call: CallbackQuery, db: Database) -> None:
    link = (await db.get_setting("channel_link")).strip()
    if not link:
        await call.answer("📢 Kanal havolasi hali belgilanmagan.", show_alert=True)
        return
    await call.message.answer("📢 Bizning kanalimizga obuna bo‘ling:", reply_markup=channel_kb(link))
    await call.answer()


@router.callback_query(F.data == "noop")
async def noop(call: CallbackQuery) -> None:
    await call.answer()
