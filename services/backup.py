"""Baza zaxira nusxalari: yaratish, tekshirish, tarix, tiklash, avtomatik jadval."""
import asyncio
import logging
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile

from database import Database

log = logging.getLogger(__name__)

UZ_TZ = timezone(timedelta(hours=5))  # O'zbekiston vaqti
AUTO_HOURS = (0, 12)                  # 00:00 va 12:00
KEEP_AUTO = 20                        # avtomatik nusxalardan nechtasi saqlanadi
NAME_RE = re.compile(r"kino_\d{8}_\d{6}_(manual|auto|prerestore)\.db")
REQUIRED_TABLES = {"users", "movies", "favorites", "admins", "channels", "movie_views", "settings"}
REQUIRED_MOVIE_COLS = {"code", "name", "poster_file_id", "video_file_id", "rating"}


def backup_dir(db: Database) -> Path:
    d = db.path.parent / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def is_valid_name(name: str) -> bool:
    return bool(NAME_RE.fullmatch(name))


async def create_backup(db: Database, kind: str = "manual") -> Path:
    name = f"kino_{datetime.now(UZ_TZ):%Y%m%d_%H%M%S}_{kind}.db"
    path = backup_dir(db) / name
    await asyncio.to_thread(db.backup_to, path)
    if kind != "manual":
        await asyncio.to_thread(prune, db)
    return path


def list_backups(db: Database) -> list[Path]:
    """Eng yangisi birinchi."""
    files = [p for p in backup_dir(db).iterdir() if is_valid_name(p.name)]
    return sorted(files, key=lambda p: p.name, reverse=True)


def prune(db: Database) -> None:
    auto = [p for p in list_backups(db) if not p.name.endswith("_manual.db")]
    for old in auto[KEEP_AUTO:]:
        old.unlink(missing_ok=True)


def delete_backup(db: Database, name: str) -> bool:
    if not is_valid_name(name):
        return False
    path = backup_dir(db) / name
    if not path.exists():
        return False
    path.unlink()
    return True


def pretty(path: Path) -> str:
    m = re.match(r"kino_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_(\w+)\.db", path.name)
    kinds = {"manual": "qo‘lda", "auto": "avto", "prerestore": "tiklashdan oldin"}
    size = path.stat().st_size / 1024
    size_txt = f"{size:.0f} KB" if size < 1024 else f"{size / 1024:.1f} MB"
    y, mo, d, h, mi, s, kind = m.groups()
    return f"{d}.{mo}.{y} {h}:{mi} ({kinds.get(kind, kind)}, {size_txt})"


def inspect_backup(path: Path) -> dict:
    """Fayl haqiqiy kino-bot bazasi ekanini tekshiradi. Noto'g'ri bo'lsa ValueError."""
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error as e:
        raise ValueError("Fayl ochilmadi") from e
    try:
        try:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Baza fayli buzilgan")
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not REQUIRED_TABLES <= tables:
                raise ValueError("Bu Kino Bot bazasi emas (jadvallar yetishmaydi)")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(movies)")}
            if not REQUIRED_MOVIE_COLS <= cols:
                raise ValueError("Bu Kino Bot bazasi emas (movies jadvali mos emas)")
            has_name_lower = "name_lower" in cols
            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            movies = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
        except sqlite3.DatabaseError as e:
            raise ValueError("Fayl SQLite bazasi emas yoki buzilgan") from e
    finally:
        conn.close()
    return {"users": users, "movies": movies, "has_name_lower": has_name_lower}


async def restore(db: Database, src: Path, admin_ids) -> Path:
    """Avval joriy bazadan zaxira oladi, so'ng src bilan almashtiradi. Qaytaradi: avto-zaxira yo'li."""
    safety = await create_backup(db, "prerestore")
    await db.restore_from(src)
    await db.init(admin_ids)  # yetishmayotgan jadval/ustunlarni tekshiradi, asosiy adminlarni qaytaradi
    await _ensure_name_lower(db)
    return safety


async def _ensure_name_lower(db: Database) -> None:
    from utils.text import normalize
    rows = await db.fetch_all("SELECT id, name FROM movies WHERE name_lower = ''")
    for r in rows:
        await db.execute("UPDATE movies SET name_lower = ? WHERE id = ?", (normalize(r["name"]), r["id"]))


# ---------------- avtomatik zaxira ----------------
def seconds_until_next(now: datetime | None = None) -> float:
    now = now or datetime.now(UZ_TZ)
    candidates = []
    for day in (0, 1):
        for h in AUTO_HOURS:
            t = (now + timedelta(days=day)).replace(hour=h, minute=0, second=0, microsecond=0)
            if t > now:
                candidates.append(t)
    return (min(candidates) - now).total_seconds()


async def send_backup(bot: Bot, path: Path, admin_ids, caption: str) -> None:
    for admin_id in admin_ids:
        try:
            await bot.send_document(admin_id, FSInputFile(path), caption=caption)
        except TelegramAPIError as e:
            log.warning("Zaxirani adminga (%s) yuborib bo'lmadi: %s", admin_id, e)


async def auto_backup_loop(bot: Bot, db: Database, admin_ids) -> None:
    while True:
        await asyncio.sleep(seconds_until_next())
        try:
            path = await create_backup(db, "auto")
            await send_backup(bot, path, admin_ids, f"💾 Avtomatik zaxira\n{pretty(path)}")
            log.info("Avtomatik zaxira olindi: %s", path.name)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Avtomatik zaxirada xato")
        await asyncio.sleep(5)  # bir xil soniyada ikki marta ishlamasligi uchun
