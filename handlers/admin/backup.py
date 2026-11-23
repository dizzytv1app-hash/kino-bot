"""Zaxira nusxalar: olish, tiklash, tarix."""
import logging
import tempfile
from pathlib import Path

from aiogram import Bot, F
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import Config
from database import Database
from keyboards.admin_kb import (back_kb, backup_history_kb, backup_menu_kb, cancel_kb,
                                restore_confirm_kb)
from services import backup as bk
from services import subscription as sub_service
from states.admin import RestoreBackup
from utils.filters import make_admin_router
from utils.tg import safe_edit

log = logging.getLogger(__name__)
router = make_admin_router("admin_backup")
MAX_RESTORE_SIZE = 20 * 1024 * 1024  # Bot API orqali yuklab olish chegarasi


@router.callback_query(F.data == "adm:backup")
async def backup_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(
        call,
        "💾 Zaxira nusxalar\n\nAvtomatik zaxira: har kuni 00:00 va 12:00 (O‘zbekiston vaqti), adminlarga yuboriladi.",
        backup_menu_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "adm:bk_make")
async def make_backup(call: CallbackQuery, db: Database, bot: Bot) -> None:
    await call.answer("💾 Tayyorlanmoqda...")
    path = await bk.create_backup(db, "manual")
    try:
        await bot.send_document(call.from_user.id, FSInputFile(path), caption=f"💾 Zaxira nusxa\n{bk.pretty(path)}")
    except TelegramAPIError:
        log.exception("Zaxirani yuborib bo'lmadi")
        await call.message.answer("⚠️ Zaxira serverda saqlandi, lekin faylni yuborib bo‘lmadi (hajmi katta bo‘lishi mumkin).", reply_markup=back_kb())
        return
    await call.message.answer("✅ Zaxira nusxa tayyor.", reply_markup=back_kb())


# ---------- tarix ----------
async def _history(call: CallbackQuery, db: Database) -> None:
    files = bk.list_backups(db)[:10]
    if not files:
        await safe_edit(call, "🗂 Zaxira tarixi bo‘sh.", backup_menu_kb())
        return
    lines = "\n".join(f"{i}. {bk.pretty(p)}" for i, p in enumerate(files, 1))
    await safe_edit(call, f"🗂 So‘nggi zaxiralar:\n\n{lines}\n\n📥 — yuklab olish, 🗑 — o‘chirish", backup_history_kb([p.name for p in files]))


@router.callback_query(F.data == "adm:bk_hist")
async def history(call: CallbackQuery, db: Database) -> None:
    await _history(call, db)
    await call.answer()


@router.callback_query(F.data.startswith("adm:bkget:"))
async def history_get(call: CallbackQuery, db: Database, bot: Bot) -> None:
    name = call.data.split(":", 2)[2]
    path = bk.backup_dir(db) / name
    if not bk.is_valid_name(name) or not path.exists():
        await call.answer("❌ Fayl topilmadi", show_alert=True)
        return
    await call.answer()
    try:
        await bot.send_document(call.from_user.id, FSInputFile(path), caption=f"💾 {bk.pretty(path)}")
    except TelegramAPIError:
        await call.message.answer("⚠️ Faylni yuborib bo‘lmadi.")


@router.callback_query(F.data.startswith("adm:bkdel:"))
async def history_delete(call: CallbackQuery, db: Database) -> None:
    ok = bk.delete_backup(db, call.data.split(":", 2)[2])
    await _history(call, db)
    await call.answer("🗑 O‘chirildi" if ok else "❌ Fayl topilmadi")


# ---------- tiklash ----------
@router.callback_query(F.data == "adm:bk_restore")
async def restore_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(RestoreBackup.file)
    await call.message.answer(
        "♻️ Tiklash uchun zaxira faylini (.db) shu yerga yuboring.\n\n"
        "⚠️ Joriy ma'lumotlar fayldagi ma'lumotlar bilan almashtiriladi. "
        "Almashtirishdan oldin joriy bazadan avtomatik zaxira olinadi.",
        reply_markup=cancel_kb(),
    )
    await call.answer()


@router.message(RestoreBackup.file, F.document)
async def restore_got_file(message: Message, state: FSMContext, bot: Bot) -> None:
    doc = message.document
    if not (doc.file_name or "").lower().endswith(".db"):
        await message.answer("❗ Faqat .db fayl yuboring.", reply_markup=cancel_kb())
        return
    if doc.file_size and doc.file_size > MAX_RESTORE_SIZE:
        await message.answer("❗ Fayl juda katta (20 MB dan oshmasligi kerak).", reply_markup=cancel_kb())
        return
    tmp = Path(tempfile.mkdtemp(prefix="kino_restore_")) / "upload.db"
    try:
        await bot.download(doc, destination=tmp)
        info = bk.inspect_backup(tmp)
    except ValueError as e:
        tmp.unlink(missing_ok=True)
        await message.answer(f"❌ {e}. Boshqa fayl yuboring.", reply_markup=cancel_kb())
        return
    except (TelegramAPIError, OSError):
        log.exception("Zaxira faylini yuklab bo'lmadi")
        await message.answer("❌ Faylni yuklab bo‘lmadi. Qayta urinib ko‘ring.", reply_markup=cancel_kb())
        return
    await state.update_data(restore_path=str(tmp))
    await state.set_state(RestoreBackup.confirm)
    await message.answer(
        "✅ Fayl tekshirildi.\n\n"
        f"👥 Foydalanuvchilar: {info['users']}\n🎬 Kinolar: {info['movies']}\n\n"
        "Joriy ma'lumotlar shu bilan almashtirilsinmi?",
        reply_markup=restore_confirm_kb(),
    )


@router.message(RestoreBackup.file)
async def restore_wrong(message: Message) -> None:
    await message.answer("❗ Iltimos, .db faylni hujjat sifatida yuboring.", reply_markup=cancel_kb())


@router.callback_query(RestoreBackup.confirm, F.data == "adm:bk_yes")
async def restore_confirm(call: CallbackQuery, state: FSMContext, db: Database, config: Config) -> None:
    path = Path((await state.get_data())["restore_path"])
    await state.clear()
    await call.answer("♻️ Tiklanmoqda...")
    try:
        safety = await bk.restore(db, path, config.admin_ids)
    except Exception:
        log.exception("Tiklashda xato")
        await call.message.answer("❌ Tiklashda xato yuz berdi. Log faylni tekshiring. Joriy baza o‘zgarmagan bo‘lishi kerak.", reply_markup=back_kb())
        return
    finally:
        path.unlink(missing_ok=True)
    sub_service.clear_cache()
    await call.message.answer(
        f"✅ Baza muvaffaqiyatli tiklandi.\n🛟 Oldingi holat saqlandi: {safety.name}",
        reply_markup=back_kb(),
    )
