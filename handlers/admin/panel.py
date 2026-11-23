from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from handlers.common import ADMIN_TEXT
from keyboards.admin_kb import admin_menu_kb
from utils.filters import make_admin_router

router = make_admin_router("admin_panel")


@router.callback_query(F.data.in_({"adm:home", "adm:cancel"}))
async def admin_home(call: CallbackQuery, state: FSMContext) -> None:
    """Admin menyusiga qaytish / har qanday jarayonni bekor qilish."""
    await state.clear()
    await call.message.answer(ADMIN_TEXT, reply_markup=admin_menu_kb())
    await call.answer()
