"""Kinolar, sevimlilar va ko'rishlar."""
from database.db import Database
from utils.text import esc_like, normalize

_EDITABLE = {"code", "name", "poster_file_id", "video_file_id", "rating"}


async def add_movie(db: Database, code: str, name: str, poster: str, video: str, rating: float) -> int:
    return await db.insert(
        "INSERT INTO movies (code, name, name_lower, poster_file_id, video_file_id, rating) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (code, name, normalize(name), poster, video, rating),
    )


async def get_by_code(db: Database, code: str) -> dict | None:
    return await db.fetch_one("SELECT * FROM movies WHERE code = ?", (code,))


async def get_by_id(db: Database, movie_id: int) -> dict | None:
    return await db.fetch_one("SELECT * FROM movies WHERE id = ?", (movie_id,))


async def code_taken(db: Database, code: str, exclude_id: int | None = None) -> bool:
    row = await db.fetch_one(
        "SELECT id FROM movies WHERE code = ? AND id != ?", (code, exclude_id or 0)
    )
    return row is not None


async def update_field(db: Database, movie_id: int, field: str, value) -> None:
    if field not in _EDITABLE:
        raise ValueError(f"Noma'lum maydon: {field}")
    if field == "name":
        await db.execute(
            "UPDATE movies SET name = ?, name_lower = ? WHERE id = ?",
            (value, normalize(value), movie_id),
        )
    else:
        await db.execute(f"UPDATE movies SET {field} = ? WHERE id = ?", (value, movie_id))


async def delete_movie(db: Database, movie_id: int) -> None:
    await db.execute("DELETE FROM movies WHERE id = ?", (movie_id,))


async def search(db: Database, query: str, limit: int = 11) -> list[dict]:
    pattern = f"%{esc_like(normalize(query))}%"
    return await db.fetch_all(
        "SELECT id, code, name, rating FROM movies "
        "WHERE name_lower LIKE ? ESCAPE '\\' ORDER BY name_lower LIMIT ?",
        (pattern, limit),
    )


async def count_movies(db: Database) -> int:
    row = await db.fetch_one("SELECT COUNT(*) AS c FROM movies")
    return row["c"]


async def latest(db: Database, limit: int, offset: int) -> list[dict]:
    """Eng oxirgi qo'shilgan kinolar birinchi."""
    return await db.fetch_all(
        "SELECT * FROM movies ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )


# ---- sevimlilar ----
async def is_favorite(db: Database, user_id: int, movie_id: int) -> bool:
    row = await db.fetch_one(
        "SELECT 1 AS ok FROM favorites WHERE user_id = ? AND movie_id = ?",
        (user_id, movie_id),
    )
    return row is not None


async def add_favorite(db: Database, user_id: int, movie_id: int) -> None:
    await db.execute(
        "INSERT OR IGNORE INTO favorites (user_id, movie_id) VALUES (?, ?)",
        (user_id, movie_id),
    )


async def remove_favorite(db: Database, user_id: int, movie_id: int) -> None:
    await db.execute(
        "DELETE FROM favorites WHERE user_id = ? AND movie_id = ?", (user_id, movie_id)
    )


async def count_favorites(db: Database, user_id: int) -> int:
    row = await db.fetch_one(
        "SELECT COUNT(*) AS c FROM favorites WHERE user_id = ?", (user_id,)
    )
    return row["c"]


async def favorites_page(db: Database, user_id: int, limit: int, offset: int) -> list[dict]:
    return await db.fetch_all(
        "SELECT m.* FROM favorites f JOIN movies m ON m.id = f.movie_id "
        "WHERE f.user_id = ? ORDER BY f.created_at DESC, m.id DESC LIMIT ? OFFSET ?",
        (user_id, limit, offset),
    )


# ---- ko'rishlar ----
async def add_view(db: Database, user_id: int, movie_id: int) -> None:
    await db.execute(
        "INSERT INTO movie_views (user_id, movie_id) VALUES (?, ?)", (user_id, movie_id)
    )
