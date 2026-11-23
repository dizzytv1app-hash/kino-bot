"""Adminlarni boshqarish."""
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Config
from database import Database
from database import users as users_db
from keyboards.admin_kb import admins_kb, cancel_kb
from states.admin import AddAdmin
from utils.filters import make_admin_router
from utils.tg import safe_edit

router = make_admin_router("admin_admins")


async def _text_and_kb(db: Database, config: Config) -> tuple[str, object]:
    ids = await users_db.list_admins(db)
    main = set(config.admin_ids)
    lines = [f"{'👑' if uid in main else '👮'} {uid}" for uid in ids]
    text = "👮 Adminlar ro‘yxati:\n\n" + "\n".join(lines) + "\n\n👑 — asosiy admin (o‘chirib bo‘lmaydi)"
    return text, admins_kb([uid for uid in ids if uid not in main])


@router.callback_query(F.data == "adm:admins")
async def admins_menu(call: CallbackQuery, db: Database, config: Config, state: FSMContext) -> None:
    await state.clear()
    text, kb = await _text_and_kb(db, config)
    await safe_edit(call, text, kb)
    await call.answer()


@router.callback_query(F.data.startswith("adm:admdel:"))
async def admin_remove(call: CallbackQuery, db: Database, config: Config) -> None:
    uid = int(call.data.split(":")[2])
    if uid in config.admin_ids:
        await call.answer("❌ Asosiy adminni o‘chirib bo‘lmaydi.", show_alert=True)
        return
    await users_db.remove_admin(db, uid)
    text, kb = await _text_and_kb(db, config)
    await safe_edit(call, text, kb)
    await call.answer("🗑 Admin o‘chirildi")


@router.callback_query(F.data == "adm:admadd")
async def admin_add_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddAdmin.waiting)
    await call.message.answer("➕ Yangi adminning Telegram ID sini yuboring (faqat raqam):", reply_markup=cancel_kb())
    await call.answer()


@router.message(AddAdmin.waiting, F.text)
async def admin_add_got(message: Message, state: FSMContext, db: Database, config: Config) -> None:
    t = message.text.strip()
    if not t.isdigit() or int(t) <= 0:
        await message.answer("❗ ID faqat musbat raqamdan iborat bo‘lishi kerak. Qayta kiriting:", reply_markup=cancel_kb())
        return
    added = await users_db.add_admin(db, int(t))
    await state.clear()
    text, kb = await _text_and_kb(db, config)
    await message.answer(("✅ Admin qo‘shildi.\n\n" if added else "ℹ️ Bu foydalanuvchi allaqachon admin.\n\n") + text, reply_markup=kb)


@router.message(AddAdmin.waiting)
async def admin_add_wrong(message: Message) -> None:
    await message.answer("❗ Iltimos, ID ni matn (raqam) ko‘rinishida yuboring.", reply_markup=cancel_kb())
