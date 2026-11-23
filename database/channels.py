"""Majburiy obuna kanallari."""
from database.db import Database


async def add_channel(db: Database, chat_id: int, title: str, link: str) -> None:
    await db.execute(
        """
        INSERT INTO channels (chat_id, title, link) VALUES (?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET title = excluded.title, link = excluded.link
        """,
        (chat_id, title, link),
    )


async def list_channels(db: Database) -> list[dict]:
    return await db.fetch_all("SELECT * FROM channels ORDER BY id")


async def remove_channel(db: Database, channel_id: int) -> None:
    await db.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
