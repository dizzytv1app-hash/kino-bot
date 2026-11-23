"""SQLite jadvallari."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    full_name   TEXT    NOT NULL DEFAULT '',
    username    TEXT,
    joined_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    last_active TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS movies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    name            TEXT    NOT NULL,
    name_lower      TEXT    NOT NULL DEFAULT '',
    poster_file_id  TEXT    NOT NULL,
    video_file_id   TEXT    NOT NULL,
    rating          REAL    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_movies_name    ON movies (name_lower);
CREATE INDEX IF NOT EXISTS idx_movies_created ON movies (created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS favorites (
    user_id    INTEGER NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    movie_id   INTEGER NOT NULL REFERENCES movies (id)     ON DELETE CASCADE,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, movie_id)
);

CREATE TABLE IF NOT EXISTS admins (
    user_id  INTEGER PRIMARY KEY,
    added_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS channels (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id  INTEGER NOT NULL UNIQUE,
    title    TEXT    NOT NULL DEFAULT '',
    link     TEXT    NOT NULL DEFAULT '',
    added_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS movie_views (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL,
    movie_id  INTEGER NOT NULL REFERENCES movies (id) ON DELETE CASCADE,
    viewed_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_views_movie ON movie_views (movie_id);
CREATE INDEX IF NOT EXISTS idx_views_date  ON movie_views (viewed_at);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
"""
