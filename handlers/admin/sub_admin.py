"""Majburiy obuna kanallarini boshqarish."""
import logging

from aiogram import Bot, F
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, MessageOriginChannel

from database import Database
from database import channels as channels_db
from keyboards.admin_kb import cancel_kb, sub_kb
from services import subscription as sub_service
from states.admin import AddChannel
from utils.filters import make_admin_router
from utils.tg import safe_edit

log = logging.getLogger(__name__)
router = make_admin_router("admin_sub")


async def _text_and_kb(db: Database) -> tuple[str, object]:
    channels = await channels_db.list_channels(db)
    if channels:
        lines = "\n".join(f"{i}. {c['title']} — {c['link']}" for i, c in enumerate(channels, 1))
        text = f"📡 Majburiy obuna kanallari ({len(channels)} ta):\n\n{lines}"
    else:
        text = "📡 Majburiy obuna kanallari yo‘q.\n\nKanal qo‘shilmaguncha obuna tekshirilmaydi."
    return text, sub_kb(channels)


@router.callback_query(F.data == "adm:sub")
async def sub_menu(call: CallbackQuery, db: Database, state: FSMContext) -> None:
    await state.clear()
    text, kb = await _text_and_kb(db)
    await safe_edit(call, text, kb)
    await call.answer()


@router.callback_query(F.data.startswith("adm:subdel:"))
async def sub_delete(call: CallbackQuery, db: Database) -> None:
    await channels_db.remove_channel(db, int(call.data.split(":")[2]))
    sub_service.clear_cache()
    text, kb = await _text_and_kb(db)
    await safe_edit(call, text, kb)
    await call.answer("🗑 Kanal o‘chirildi")


@router.callback_query(F.data == "adm:subadd")
async def sub_add_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddChannel.waiting)
    await call.message.answer(
        "➕ Kanalni qo‘shish uchun:\n"
        "• kanal @username yoki ID sini (-100...) yuboring, yoki\n"
        "• kanaldan istalgan xabarni shu yerga forward qiling.\n\n"
        "⚠️ Bot avval o‘sha kanalga ADMIN qilib qo‘shilgan bo‘lishi shart.",
        reply_markup=cancel_kb(),
    )
    await call.answer()


@router.message(AddChannel.waiting)
async def sub_add_got(message: Message, state: FSMContext, db: Database, bot: Bot) -> None:
    ident: int | str | None = None
    if isinstance(message.forward_origin, MessageOriginChannel):
        ident = message.forward_origin.chat.id
    elif message.text:
        t = message.text.strip()
        if t.startswith(("https://t.me/", "http://t.me/", "t.me/")) and "/+" not in t and "joinchat" not in t:
            t = "@" + t.rstrip("/").rsplit("/", 1)[1]
        if t.lstrip("-").isdigit():
            ident = int(t)
        elif t.startswith("@") and len(t) > 1:
            ident = t
    if ident is None:
        await message.answer("❗ Kanal @username, ID yoki forward qilingan xabar yuboring.", reply_markup=cancel_kb())
        return

    try:
        chat = await bot.get_chat(ident)
        if chat.type != ChatType.CHANNEL:
            await message.answer("❗ Bu kanal emas. Faqat kanal qo‘shish mumkin.", reply_markup=cancel_kb())
            return
        me = await bot.get_chat_member(chat.id, (await bot.me()).id)
        if me.status != ChatMemberStatus.ADMINISTRATOR:
            await message.answer("❗ Bot bu kanalda admin emas. Avval botni kanalga admin qiling, so‘ng qayta yuboring.", reply_markup=cancel_kb())
            return
        if chat.username:
            link = f"https://t.me/{chat.username}"
        else:
            link = (await bot.create_chat_invite_link(chat.id)).invite_link
    except TelegramAPIError as e:
        log.warning("Kanal qo'shishda xato (%s): %s", ident, e)
        await message.answer(
            "❗ Kanalni topib bo‘lmadi yoki havola yaratib bo‘lmadi.\n"
            "Bot kanalda admin ekanini (yopiq kanalda “taklif havolalari yaratish” huquqi bilan) tekshiring.",
            reply_markup=cancel_kb(),
        )
        return

    await channels_db.add_channel(db, chat.id, chat.title or str(chat.id), link)
    sub_service.clear_cache()
    await state.clear()
    text, kb = await _text_and_kb(db)
    await message.answer("✅ Kanal qo‘shildi.\n\n" + text, reply_markup=kb)
