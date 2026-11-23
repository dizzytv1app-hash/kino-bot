"""Majburiy obunani tekshirish."""
import logging
import time

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError

log = logging.getLogger(__name__)

_OK_TTL = 60  # soniya: obuna bo'lganlarni qayta-qayta tekshirmaslik uchun
_ok_until: dict[int, float] = {}


def _is_member(member) -> bool:
    if member.status in (ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER):
        return True
    return member.status == ChatMemberStatus.RESTRICTED and bool(getattr(member, "is_member", False))


def is_cached_ok(user_id: int) -> bool:
    return _ok_until.get(user_id, 0) > time.monotonic()


def mark_ok(user_id: int) -> None:
    _ok_until[user_id] = time.monotonic() + _OK_TTL
    if len(_ok_until) > 50_000:  # xotira o'smasligi uchun
        now = time.monotonic()
        for uid in [u for u, t in _ok_until.items() if t <= now]:
            _ok_until.pop(uid, None)


def clear_cache() -> None:
    _ok_until.clear()


async def get_missing(bot: Bot, channels: list[dict], user_id: int) -> list[dict]:
    """Foydalanuvchi obuna bo'lmagan kanallar ro'yxati."""
    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["chat_id"], user_id)
        except TelegramAPIError as e:
            # Bot kanaldan chiqarilgan bo'lishi mumkin: foydalanuvchini bloklamaymiz
            log.warning("Obunani tekshirib bo'lmadi (kanal %s): %s", ch["chat_id"], e)
            continue
        if not _is_member(member):
            missing.append(ch)
    return missing
