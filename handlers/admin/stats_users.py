from aiogram import F
from aiogram.types import CallbackQuery

from database import Database
from database import movies as movies_db
from database import stats as stats_db
from database import users as users_db
from keyboards.admin_kb import back_kb
from utils.filters import make_admin_router
from utils.tg import safe_edit

router = make_admin_router("admin_stats_users")


@router.callback_query(F.data == "adm:stats")
async def show_stats(call: CallbackQuery, db: Database) -> None:
    top = await stats_db.top_movies(db, 5)
    top_text = "\n".join(
        f"{i}. {m['name']} (🔢 {m['code']}) — {m['views']} ta" for i, m in enumerate(top, 1)
    ) or "Hozircha ko‘rishlar yo‘q"
    text = (
        "📊 Statistika\n\n"
        f"👥 Jami foydalanuvchilar: {await users_db.count_users(db)}\n"
        f"🆕 Bugungi yangi foydalanuvchilar: {await users_db.count_new_today(db)}\n"
        f"🎬 Jami kinolar: {await movies_db.count_movies(db)}\n"
        f"👁 Jami ko‘rishlar: {await stats_db.total_views(db)}\n"
        f"📅 Bugungi ko‘rishlar: {await stats_db.views_today(db)}\n\n"
        f"🔥 Eng ko‘p ko‘rilgan kinolar:\n{top_text}"
    )
    await safe_edit(call, text, back_kb())
    await call.answer()


@router.callback_query(F.data == "adm:users")
async def show_users(call: CallbackQuery, db: Database) -> None:
    recent = await users_db.recent_users(db, 10)
    lines = [
        f"• {u['user_id']} — {u['full_name'] or 'Noma’lum'}"
        + (f" (@{u['username']})" if u["username"] else "")
        for u in recent
    ]
    text = (
        "👥 Foydalanuvchilar\n\n"
        f"Jami: {await users_db.count_users(db)}\n"
        f"Bugun qo‘shilgan: {await users_db.count_new_today(db)}\n\n"
        "So‘nggi 10 ta foydalanuvchi:\n" + ("\n".join(lines) or "—")
    )
    await safe_edit(call, text, back_kb())
    await call.answer()
