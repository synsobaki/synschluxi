from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_id: int

    db_url: str = "sqlite+aiosqlite:///./umkovo_v2.db"

    # ✅ ссылка на админа/менеджера ключей (для кнопки URL)
    # Пример: https://t.me/your_admin_username  или tg://user?id=123456
    admin_url: str = "https://t.me/umkovo_support"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


def load_settings() -> Settings:
    return Settings()