"""Bot o'chirilgan bo'lsa (admin sozlamalaridan) oddiy foydalanuvchilarga xabar beradi."""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

from database import Database

MAINTENANCE_TEXT = "🛠 Bot vaqtincha texnik xizmatda. Iltimos, keyinroq urinib ko‘ring."


class MaintenanceMiddleware(BaseMiddleware):
    def __init__(self, db: Database) -> None:
        self.db = db

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        user = getattr(event, "from_user", None)
        if user and await self.db.get_setting("bot_enabled", "1") == "0" and not await self.db.is_admin(user.id):
            if isinstance(event, CallbackQuery):
                await event.answer(MAINTENANCE_TEXT, show_alert=True)
            else:
                await event.answer(MAINTENANCE_TEXT)
            return None
        return await handler(event, data)
