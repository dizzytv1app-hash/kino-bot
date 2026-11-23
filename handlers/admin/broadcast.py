from aiogram import Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message

from database import Database
from database import users as users_db
from keyboards.admin_kb import back_kb, broadcast_confirm_kb, cancel_kb
from services.broadcast import start_broadcast
from states.admin import Broadcast
from utils.filters import make_admin_router

router = make_admin_router("admin_broadcast")


@router.callback_query(F.data == "adm:broadcast")
async def bc_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Broadcast.message)
    await call.message.answer(
        "📢 Reklama xabarini yuboring (matn, rasm, video va h.k.).\nU barcha foydalanuvchilarga aynan shu ko‘rinishda yuboriladi.",
        reply_markup=cancel_kb(),
    )
    await call.answer()


@router.message(Broadcast.message)
async def bc_got_message(message: Message, state: FSMContext, db: Database, bot: Bot) -> None:
    await state.update_data(src_chat=message.chat.id, src_msg=message.message_id)
    await state.set_state(Broadcast.confirm)
    try:
        await bot.copy_message(message.chat.id, message.chat.id, message.message_id)  # ko'rinish (preview)
    except TelegramAPIError:
        await message.answer("❗ Bu xabarni reklama sifatida yuborib bo‘lmaydi. Boshqa xabar yuboring.", reply_markup=cancel_kb())
        await state.set_state(Broadcast.message)
        return
    total = len(await users_db.all_user_ids(db))
    await message.answer(
        f"👆 Reklama shunday ko‘rinadi.\n👥 Qabul qiluvchilar: {total} ta\n\nYuborilsinmi?",
        reply_markup=broadcast_confirm_kb(),
    )


@router.callback_query(Broadcast.confirm, F.data == "adm:bc_yes")
async def bc_confirm(call: CallbackQuery, state: FSMContext, db: Database, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    start_broadcast(bot, db, call.from_user.id, data["src_chat"], data["src_msg"])
    await call.message.answer("📤 Reklama yuborish boshlandi. Tugagach hisobot keladi.", reply_markup=back_kb())
    await call.answer()
