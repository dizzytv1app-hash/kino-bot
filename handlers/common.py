"""/start va /admin buyruqlari (har qanday holatda ishlaydi)."""
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import Database
from keyboards.admin_kb import admin_menu_kb
from keyboards.user_kb import main_menu_kb

router = Router(name="common")

WELCOME_TEXT = (
    "🎬 KINO BOT ga xush kelibsiz!\n\n"
    "Assalomu alaykum! 👋\n\n"
    "Bu bot orqali o‘zingizga yoqqan kinolarni tez va oson topishingiz mumkin.\n\n"
    "🍿 Yoqimli tomosha tilaymiz!"
)
ADMIN_TEXT = "👨‍💼 Admin panel\n\nKerakli bo‘limni tanlang:"


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    if not await db.is_admin(message.from_user.id):
        await message.answer("⛔ Bu bo‘lim faqat adminlar uchun.")
        return
    await message.answer(ADMIN_TEXT, reply_markup=admin_menu_kb())
