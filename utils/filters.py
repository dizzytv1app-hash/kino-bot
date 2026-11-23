from aiogram import Router
from aiogram.filters import Filter
from aiogram.types import TelegramObject

from database import Database


class IsAdmin(Filter):
    async def __call__(self, event: TelegramObject, db: Database) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and await db.is_admin(user.id))


def make_admin_router(name: str) -> Router:
    """Faqat adminlar uchun router."""
    router = Router(name=name)
    router.message.filter(IsAdmin())
    router.callback_query.filter(IsAdmin())
    return router
