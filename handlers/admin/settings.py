"""Bot sozlamalari: bot holati va kanal havolasi."""
import logging
import re

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import Database
from keyboards.admin_kb import cancel_kb, settings_kb
from states.admin import SetChannelLink
from utils.filters import make_admin_router
from utils.tg import safe_edit

log = logging.getLogger(__name__)
router = make_admin_router("admin_settings")
_URL_RE = re.compile(r"https?://\S+")


async def _view(db: Database) -> tuple[str, object]:
    enabled = await db.get_setting("bot_enabled", "1") == "1"
    link = (await db.get_setting("channel_link")).strip()
    text = (
        "⚙️ Bot sozlamalari\n\n"
        f"🤖 Bot holati: {'🟢 yoqilgan' if enabled else '🔴 o‘chirilgan (faqat adminlar ishlata oladi)'}\n"
        f"📢 Kanal havolasi: {link or '❌ belgilanmagan'}"
    )
    return text, settings_kb(enabled, bool(link))


@router.callback_query(F.data == "adm:settings")
async def settings_menu(call: CallbackQuery, db: Database, state: FSMContext) -> None:
    await state.clear()
    text, kb = await _view(db)
    await safe_edit(call, text, kb)
    await call.answer()


@router.callback_query(F.data == "adm:set_toggle")
async def toggle_bot(call: CallbackQuery, db: Database) -> None:
    enabled = await db.get_setting("bot_enabled", "1") == "1"
    await db.set_setting("bot_enabled", "0" if enabled else "1")
    text, kb = await _view(db)
    await safe_edit(call, text, kb)
    await call.answer("🔴 Bot o‘chirildi" if enabled else "🟢 Bot yoqildi")


@router.callback_query(F.data == "adm:set_link")
async def link_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SetChannelLink.waiting)
    await call.message.answer(
        "📢 Kanal havolasini yuboring (masalan https://t.me/kanal_nomi yoki @kanal_nomi):",
        reply_markup=cancel_kb(),
    )
    await call.answer()


@router.message(SetChannelLink.waiting, F.text)
async def link_got(message: Message, state: FSMContext, db: Database) -> None:
    t = message.text.strip()
    if re.fullmatch(r"@[A-Za-z0-9_]{4,}", t):
        t = f"https://t.me/{t[1:]}"
    elif t.startswith("t.me/"):
        t = "https://" + t
    if not _URL_RE.fullmatch(t):
        await message.answer("❗ Havola noto‘g‘ri. https://t.me/... yoki @username yuboring:", reply_markup=cancel_kb())
        return
    await db.set_setting("channel_link", t)
    await state.clear()
    text, kb = await _view(db)
    await message.answer("✅ Kanal havolasi saqlandi.\n\n" + text, reply_markup=kb)


@router.message(SetChannelLink.waiting)
async def link_wrong(message: Message) -> None:
    await message.answer("❗ Iltimos, havolani matn ko‘rinishida yuboring.", reply_markup=cancel_kb())


@router.callback_query(F.data == "adm:set_link_del")
async def link_delete(call: CallbackQuery, db: Database) -> None:
    await db.set_setting("channel_link", "")
    text, kb = await _view(db)
    await safe_edit(call, text, kb)
    await call.answer("🗑 Havola o‘chirildi")
