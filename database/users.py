"""Foydalanuvchilar va adminlar."""
from database.db import Database

_TODAY = "date({col}, '+5 hours') = date('now', '+5 hours')"  # O'zbekiston vaqti (UTC+5)


async def count_users(db: Database) -> int:
    return (await db.fetch_one("SELECT COUNT(*) AS c FROM users"))["c"]


async def count_new_today(db: Database) -> int:
    row = await db.fetch_one(
        f"SELECT COUNT(*) AS c FROM users WHERE {_TODAY.format(col='joined_at')}"
    )
    return row["c"]


async def recent_users(db: Database, limit: int = 10) -> list[dict]:
    return await db.fetch_all(
        "SELECT user_id, full_name, username, joined_at FROM users "
        "ORDER BY joined_at DESC, user_id DESC LIMIT ?",
        (limit,),
    )


async def all_user_ids(db: Database) -> list[int]:
    rows = await db.fetch_all("SELECT user_id FROM users")
    return [r["user_id"] for r in rows]


# ---- adminlar ----
async def list_admins(db: Database) -> list[int]:
    rows = await db.fetch_all("SELECT user_id FROM admins ORDER BY added_at, user_id")
    return [r["user_id"] for r in rows]


async def add_admin(db: Database, user_id: int) -> bool:
    """Yangi qo'shilsa True, avvaldan bor bo'lsa False."""
    return await db.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,)) > 0


async def remove_admin(db: Database, user_id: int) -> None:
    await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
