"""Matn yordamchilari."""
import math
import re

_APOS = str.maketrans({"ʻ": "'", "ʼ": "'", "‘": "'", "’": "'", "`": "'", "´": "'"})
_CODE_RE = re.compile(r"[A-Za-z0-9_\-]{1,20}")


def normalize(text: str) -> str:
    """Qidiruv uchun: kichik harf, bir xil apostrof, ortiqcha bo'shliqsiz."""
    return " ".join(text.translate(_APOS).casefold().split())


def esc_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def valid_code(text: str) -> bool:
    return bool(_CODE_RE.fullmatch(text))


def parse_rating(text: str) -> float | None:
    try:
        value = float(text.strip().replace(",", "."))
    except ValueError:
        return None
    if not math.isfinite(value) or not 0 <= value <= 10:
        return None
    return round(value, 1)


def format_rating(rating: float) -> str:
    return f"{rating:.1f}/10"


def movie_caption(movie: dict) -> str:
    return (
        f"🎬 {movie['name']}\n\n"
        f"🔢 Kodi: {movie['code']}\n"
        f"⭐ Reytingi: {format_rating(movie['rating'])}"
    )
