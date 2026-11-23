from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery

from database import Database
from database import channels as channels_db
from handlers.common import WELCOME_TEXT
from keyboards.user_kb import main_menu_kb
from services import subscription as sub_service

router = Router(name="check_sub")


@router.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery, db: Database, bot: Bot) -> None:
    channels = await channels_db.list_channels(db)
    missing = await sub_service.get_missing(bot, channels, call.from_user.id)
    if missing:
        await call.answer("❌ Siz hali barcha kanallarga obuna bo‘lmagansiz.", show_alert=True)
        return
    sub_service.mark_ok(call.from_user.id)
    try:
        await call.message.delete()
    except TelegramAPIError:
        pass
    await call.message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())
    await call.answer("✅ Rahmat!")
