"""Statistika."""
from database.db import Database

_TODAY = "date(viewed_at, '+5 hours') = date('now', '+5 hours')"


async def total_views(db: Database) -> int:
    return (await db.fetch_one("SELECT COUNT(*) AS c FROM movie_views"))["c"]


async def views_today(db: Database) -> int:
    return (await db.fetch_one(f"SELECT COUNT(*) AS c FROM movie_views WHERE {_TODAY}"))["c"]


async def top_movies(db: Database, limit: int = 5) -> list[dict]:
    return await db.fetch_all(
        "SELECT m.code, m.name, COUNT(v.id) AS views FROM movie_views v "
        "JOIN movies m ON m.id = v.movie_id GROUP BY m.id "
        "ORDER BY views DESC, m.id DESC LIMIT ?",
        (limit,),
    )
