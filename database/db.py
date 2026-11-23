"""SQLite bilan asinxron ishlash (stdlib sqlite3 + asyncio.to_thread)."""
import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .schema import SCHEMA

log = logging.getLogger(__name__)


class Database:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = asyncio.Lock()  # yozuvlarni ketma-ket bajarish uchun

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    # ---- past darajadagi yordamchilar ----
    def _run(self, sql: str, params: Iterable[Any], mode: str):
        conn = self._connect()
        try:
            cur = conn.execute(sql, tuple(params))
            if mode == "one":
                row = cur.fetchone()
                return dict(row) if row else None
            if mode == "all":
                return [dict(r) for r in cur.fetchall()]
            conn.commit()
            return cur.lastrowid if mode == "insert" else cur.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    async def fetch_one(self, sql: str, params: Iterable[Any] = ()) -> dict | None:
        return await asyncio.to_thread(self._run, sql, params, "one")

    async def fetch_all(self, sql: str, params: Iterable[Any] = ()) -> list[dict]:
        return await asyncio.to_thread(self._run, sql, params, "all")

    async def execute(self, sql: str, params: Iterable[Any] = ()) -> int:
        async with self._lock:
            return await asyncio.to_thread(self._run, sql, params, "write")

    async def insert(self, sql: str, params: Iterable[Any] = ()) -> int:
        async with self._lock:
            return await asyncio.to_thread(self._run, sql, params, "insert")

    def backup_to(self, dst: Path) -> None:
        """Bazaning xavfsiz nusxasini (ishlayotgan paytda ham) dst ga saqlaydi."""
        src_conn = self._connect()
        dst_conn = sqlite3.connect(dst)
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()

    def _restore(self, src: Path) -> None:
        src_conn = sqlite3.connect(src)
        dst_conn = sqlite3.connect(self.path, timeout=30)
        try:
            try:
                # sahifa o'lchami farq qilsa WAL rejimida backup xato beradi
                dst_conn.execute("PRAGMA journal_mode = DELETE")
            except sqlite3.OperationalError:
                pass  # boshqa ulanish band: joriy rejimda davom etamiz
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()

    async def restore_from(self, src: Path) -> None:
        """Bazani src fayl bilan almashtiradi (yozuvlar to'xtatilgan holda)."""
        async with self._lock:
            await asyncio.to_thread(self._restore, src)

    # ---- ishga tushirish ----
    @staticmethod
    def _migrate(conn: sqlite3.Connection) -> None:
        """Eski tuzilishdagi bazalarni (masalan eski zaxiradan tiklanganda) yangilaydi."""
        cols = {r[1] for r in conn.execute("PRAGMA table_info(movies)")}
        if cols and "name_lower" not in cols:
            conn.execute("ALTER TABLE movies ADD COLUMN name_lower TEXT NOT NULL DEFAULT ''")
            conn.commit()

    def _init_schema(self, admin_ids: Iterable[int]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            self._migrate(conn)
            conn.executescript(SCHEMA)
            conn.executemany(
                "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
                [(int(a),) for a in admin_ids],
            )
            conn.commit()
        finally:
            conn.close()

    async def init(self, admin_ids: Iterable[int]) -> None:
        await asyncio.to_thread(self._init_schema, list(admin_ids))
        log.info("Ma'lumotlar bazasi tayyor: %s", self.path)

    # ---- foydalanuvchilar ----
    async def upsert_user(
        self, user_id: int, full_name: str, username: str | None
    ) -> None:
        await self.execute(
            """
            INSERT INTO users (user_id, full_name, username)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                username = excluded.username,
                last_active = datetime('now')
            """,
            (user_id, full_name, username),
        )

    async def is_admin(self, user_id: int) -> bool:
        row = await self.fetch_one(
            "SELECT 1 AS ok FROM admins WHERE user_id = ?", (user_id,)
        )
        return row is not None

    # ---- sozlamalar ----
    async def get_setting(self, key: str, default: str = "") -> str:
        row = await self.fetch_one(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        return row["value"] if row else default

    async def set_setting(self, key: str, value: str) -> None:
        await self.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
