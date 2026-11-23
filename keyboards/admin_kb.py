from aiogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M

_MENU = B(text="⬅️ Admin menyu", callback_data="adm:home")
_CANCEL = B(text="❌ Bekor qilish", callback_data="adm:cancel")

FIELD_LABELS = {
    "code": "🔢 Kino kodi",
    "name": "📝 Kino nomi",
    "poster": "🖼 Poster",
    "video": "🎥 Video",
    "rating": "⭐ Reyting",
}


def admin_menu_kb() -> M:
    return M(inline_keyboard=[
        [B(text="🎬 Kino qo‘shish", callback_data="adm:movie_add"),
         B(text="✏️ Kinoni tahrirlash", callback_data="adm:movie_edit")],
        [B(text="🗑 Kinoni o‘chirish", callback_data="adm:movie_delete"),
         B(text="📋 Kinolar ro‘yxati", callback_data="adm:movie_list")],
        [B(text="📊 Statistika", callback_data="adm:stats"),
         B(text="👥 Foydalanuvchilar", callback_data="adm:users")],
        [B(text="📢 Reklama yuborish", callback_data="adm:broadcast"),
         B(text="📡 Majburiy obuna", callback_data="adm:sub")],
        [B(text="👮 Adminlarni boshqarish", callback_data="adm:admins"),
         B(text="⚙️ Bot sozlamalari", callback_data="adm:settings")],
        [B(text="💾 Zaxira nusxalar", callback_data="adm:backup")],
    ])


def cancel_kb() -> M:
    return M(inline_keyboard=[[_CANCEL]])


def back_kb() -> M:
    return M(inline_keyboard=[[_MENU]])


def confirm_add_kb() -> M:
    return M(inline_keyboard=[
        [B(text="✅ Saqlash", callback_data="adm:add_save")],
        [B(text="✏️ Tahrirlash", callback_data="adm:add_edit"),
         B(text="❌ Bekor qilish", callback_data="adm:cancel")],
    ])


def fields_kb(prefix: str, back_data: str | None = None, back_text: str = "⬅️ Orqaga") -> M:
    rows = [[B(text=label, callback_data=f"{prefix}:{key}")] for key, label in FIELD_LABELS.items()]
    if back_data:
        rows.append([B(text=back_text, callback_data=back_data)])
    rows.append([_CANCEL])
    return M(inline_keyboard=rows)


def confirm_delete_kb() -> M:
    return M(inline_keyboard=[
        [B(text="🗑 Ha, o‘chirish", callback_data="adm:del_yes")],
        [_CANCEL],
    ])


def pager_kb(page: int, pages: int, prefix: str) -> M:
    nav = []
    if page > 0:
        nav.append(B(text="⬅️", callback_data=f"{prefix}:{page - 1}"))
    nav.append(B(text=f"{page + 1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(B(text="➡️", callback_data=f"{prefix}:{page + 1}"))
    return M(inline_keyboard=[nav, [_MENU]])


def broadcast_confirm_kb() -> M:
    return M(inline_keyboard=[
        [B(text="✅ Yuborish", callback_data="adm:bc_yes")],
        [_CANCEL],
    ])


def sub_kb(channels: list[dict]) -> M:
    rows = [[B(text=f"🗑 {c['title'] or c['chat_id']}", callback_data=f"adm:subdel:{c['id']}")] for c in channels]
    rows.append([B(text="➕ Kanal qo‘shish", callback_data="adm:subadd")])
    rows.append([_MENU])
    return M(inline_keyboard=rows)


def admins_kb(removable: list[int]) -> M:
    rows = [[B(text=f"🗑 {uid}", callback_data=f"adm:admdel:{uid}")] for uid in removable]
    rows.append([B(text="➕ Admin qo‘shish", callback_data="adm:admadd")])
    rows.append([_MENU])
    return M(inline_keyboard=rows)


def settings_kb(bot_enabled: bool, has_link: bool) -> M:
    rows = [
        [B(text="🔴 Botni o‘chirish" if bot_enabled else "🟢 Botni yoqish", callback_data="adm:set_toggle")],
        [B(text="📢 Kanal havolasini o‘zgartirish", callback_data="adm:set_link")],
    ]
    if has_link:
        rows.append([B(text="🗑 Kanal havolasini o‘chirish", callback_data="adm:set_link_del")])
    rows.append([_MENU])
    return M(inline_keyboard=rows)


def backup_menu_kb() -> M:
    return M(inline_keyboard=[
        [B(text="📥 Zaxira nusxa olish", callback_data="adm:bk_make")],
        [B(text="♻️ Zaxiradan tiklash", callback_data="adm:bk_restore")],
        [B(text="🗂 Zaxira tarixi", callback_data="adm:bk_hist")],
        [_MENU],
    ])


def backup_history_kb(files: list[str]) -> M:
    rows = []
    for i, name in enumerate(files, 1):
        rows.append([B(text=f"📥 {i}", callback_data=f"adm:bkget:{name}"),
                     B(text=f"🗑 {i}", callback_data=f"adm:bkdel:{name}")])
    rows.append([B(text="⬅️ Zaxira menyusi", callback_data="adm:backup")])
    return M(inline_keyboard=rows)


def restore_confirm_kb() -> M:
    return M(inline_keyboard=[
        [B(text="✅ Ha, tiklash", callback_data="adm:bk_yes")],
        [_CANCEL],
    ])
