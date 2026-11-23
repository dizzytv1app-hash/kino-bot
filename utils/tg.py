"""Telegram uchun kichik yordamchilar."""
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery


async def safe_edit(call: CallbackQuery, text: str, reply_markup=None) -> None:
    """Xabarni tahrirlaydi; imkoni bo'lmasa (masalan rasmli xabar) yangisini yuboradi."""
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        await call.message.answer(text, reply_markup=reply_markup)
