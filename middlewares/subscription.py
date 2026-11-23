"""Majburiy obuna: kanalga a'zo bo'lmagan foydalanuvchini to'xtatadi."""
from typing import Any, Awaitable, Callable

from aiogram import Bot, BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

from database import Database
from database import channels as channels_db
from keyboards.user_kb import check_sub_kb
from services import subscription as sub_service

PROMPT = "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling, so‘ng “✅ Tekshirish” tugmasini bosing:"


class SubscriptionMiddleware(BaseMiddleware):
    def __init__(self, db: Database) -> None:
        self.db = db

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        user = getattr(event, "from_user", None)
        if user is None or (isinstance(event, CallbackQuery) and event.data == "check_sub"):
            return await handler(event, data)
        if sub_service.is_cached_ok(user.id) or await self.db.is_admin(user.id):
            return await handler(event, data)

        channels = await channels_db.list_channels(self.db)
        if not channels:
            return await handler(event, data)

        bot: Bot = data["bot"]
        missing = await sub_service.get_missing(bot, channels, user.id)
        if not missing:
            sub_service.mark_ok(user.id)
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer()
            await event.message.answer(PROMPT, reply_markup=check_sub_kb(missing))
        else:
            await event.answer(PROMPT, reply_markup=check_sub_kb(missing))
        return None
