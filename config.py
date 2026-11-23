"""Bot konfiguratsiyasi (.env dan o'qiladi)."""
from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Kodga o'rnatilgan bosh adminlar (.env dagi ADMIN_IDS ga qo'shimcha; o'chirib bo'lmaydi)
DEFAULT_ADMIN_IDS: tuple[int, ...] = (6222096713,)
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: tuple[int, ...]
    db_path: Path
    logs_dir: Path
    port: int | None


def _parse_ids(raw: str) -> tuple[int, ...]:
    ids = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part:
            if not part.lstrip("-").isdigit():
                raise RuntimeError(f"ADMIN_IDS da noto'g'ri qiymat: {part!r}")
            ids.append(int(part))
    return tuple(ids)


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or token.startswith("123456789:AAxxx"):
        raise RuntimeError(".env faylida BOT_TOKEN to'g'ri kiritilmagan.")

    admin_ids = tuple(dict.fromkeys(DEFAULT_ADMIN_IDS + _parse_ids(os.getenv("ADMIN_IDS", ""))))

    db_path = Path(os.getenv("DB_PATH", "data/kino_bot.db"))
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path

    return Config(
        bot_token=token,
        admin_ids=admin_ids,
        db_path=db_path,
        logs_dir=BASE_DIR / "logs",
        port=int(os.getenv("PORT")) if os.getenv("PORT", "").isdigit() else None,
    )
