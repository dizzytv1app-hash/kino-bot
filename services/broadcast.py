"""Reklama yuborish (barcha foydalanuvchilarga)."""
import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter

from database import Database
from database import users as users_db

log = logging.getLogger(__name__)
_tasks: set[asyncio.Task] = set()


async def _copy(bot: Bot, uid: int, src_chat: int, src_msg: int) -> bool:
    try:
        await bot.copy_message(uid, src_chat, src_msg)
        return True
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        try:
            await bot.copy_message(uid, src_chat, src_msg)
            return True
        except TelegramAPIError:
            return False
    except TelegramAPIError:
        return False  # bot bloklangan, chat topilmadi va h.k.
    except Exception:
        log.exception("Reklama yuborishda kutilmagan xato (uid=%s)", uid)
        return False


async def _run(bot: Bot, db: Database, admin_id: int, src_chat: int, src_msg: int) -> None:
    ok = fail = 0
    for uid in await users_db.all_user_ids(db):
        if await _copy(bot, uid, src_chat, src_msg):
            ok += 1
        else:
            fail += 1
        await asyncio.sleep(0.05)  # Telegram limiti (~30 xabar/soniya)
    try:
        await bot.send_message(
            admin_id, f"📢 Reklama yuborish yakunlandi\n\n✅ Yuborildi: {ok}\n❌ Yuborilmadi: {fail}"
        )
    except TelegramAPIError:
        log.exception("Reklama hisobotini yuborib bo'lmadi")


def start_broadcast(bot: Bot, db: Database, admin_id: int, src_chat: int, src_msg: int) -> None:
    task = asyncio.create_task(_run(bot, db, admin_id, src_chat, src_msg))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
