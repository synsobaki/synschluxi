import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Settings:
    bot_token: str
    admin_id: int
    db_url: str = "sqlite+aiosqlite:///./umkovo_v2.db"

    # ✅ ссылка на админа/менеджера ключей (для кнопки URL)
    # Пример: https://t.me/your_admin_username  или tg://user?id=123456
    admin_url: str = "https://t.me/umkovo_support"


def load_settings() -> Settings:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    admin_id_raw = os.getenv("ADMIN_ID")

    if not bot_token:
        raise ValueError("BOT_TOKEN is required")
    if not admin_id_raw:
        raise ValueError("ADMIN_ID is required")

    return Settings(
        bot_token=bot_token,
        admin_id=int(admin_id_raw),
        db_url=os.getenv("DB_URL", "sqlite+aiosqlite:///./umkovo_v2.db"),
        admin_url=os.getenv("ADMIN_URL", "https://t.me/umkovo_support"),
    )
