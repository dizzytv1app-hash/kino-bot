"""Har bir xabar/tugma bosilganda foydalanuvchini bazaga yozadi."""
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database import Database

log = logging.getLogger(__name__)


class UserTrackerMiddleware(BaseMiddleware):
    def __init__(self, db: Database) -> None:
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user and not user.is_bot:
            try:
                await self.db.upsert_user(user.id, user.full_name, user.username)
            except Exception:
                log.exception("Foydalanuvchini saqlashda xato (id=%s)", user.id)
        return await handler(event, data)
