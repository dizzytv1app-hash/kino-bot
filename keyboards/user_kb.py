from aiogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M

from utils.text import format_rating

_HOME = B(text="🏠 Bosh menyu", callback_data="menu:home")


def main_menu_kb() -> M:
    """Asosiy menyu: 2 qator x 2 ustun."""
    return M(inline_keyboard=[
        [B(text="🔎 Kino qidirish", callback_data="menu:search"),
         B(text="❤️ Sevimlilar", callback_data="menu:favorites")],
        [B(text="📢 Bizning kanal", callback_data="menu:channel"),
         B(text="🆕 Yangi kinolar", callback_data="menu:new")],
    ])


def home_kb() -> M:
    return M(inline_keyboard=[[_HOME]])


def search_again_kb() -> M:
    return M(inline_keyboard=[[B(text="🔎 Qayta qidirish", callback_data="menu:search")], [_HOME]])


def channel_kb(url: str) -> M:
    return M(inline_keyboard=[[B(text="📢 Kanalga o‘tish", url=url)]])


def check_sub_kb(channels: list[dict]) -> M:
    rows = [[B(text=f"📢 {c['title'] or 'Kanal'}", url=c["link"])] for c in channels]
    rows.append([B(text="✅ Tekshirish", callback_data="check_sub")])
    return M(inline_keyboard=rows)


def movie_kb(movie_id: int, is_fav: bool, show_watch: bool) -> M:
    rows = []
    if show_watch:
        rows.append([B(text="▶️ Ko‘rish", callback_data=f"watch:{movie_id}")])
    fav_text = "💔 Sevimlilardan o‘chirish" if is_fav else "❤️ Sevimlilarga qo‘shish"
    rows.append([B(text=fav_text, callback_data=f"fav:t:{movie_id}:{int(show_watch)}")])
    rows.append([_HOME])
    return M(inline_keyboard=rows)


def select_kb(movie_id: int) -> M:
    return M(inline_keyboard=[[B(text="🎬 Tanlash", callback_data=f"movie:{movie_id}")]])


def _nav_row(page: int, pages: int, prefix: str) -> list[B]:
    row = []
    if page > 0:
        row.append(B(text="⬅️ Oldingi", callback_data=f"{prefix}:{page - 1}"))
    row.append(B(text=f"{page + 1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        row.append(B(text="Keyingi ➡️", callback_data=f"{prefix}:{page + 1}"))
    return row


def movies_kb(movies: list[dict], page: int = 0, pages: int = 1, prefix: str = "") -> M:
    """Kinolar ro'yxati (har biri alohida tugma) + sahifalash."""
    rows = [
        [B(text=f"🎬 {m['name']} ⭐ {m['rating']:.1f}", callback_data=f"movie:{m['id']}")]
        for m in movies
    ]
    if pages > 1:
        rows.append(_nav_row(page, pages, prefix))
    rows.append([_HOME])
    return M(inline_keyboard=rows)


def new_nav_kb(page: int, pages: int) -> M:
    rows = []
    if pages > 1:
        rows.append(_nav_row(page, pages, "new"))
    rows.append([_HOME])
    return M(inline_keyboard=rows)
