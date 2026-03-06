# src/infrastructure/db.py
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import load_settings

Base = declarative_base()

_engine: AsyncEngine | None = None

AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Backward-compatible alias used by the app entrypoint/middlewares.
async_sessionmaker = AsyncSessionLocal


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = load_settings()

        # ВАЖНО для SQLite:
        # - busy_timeout: ждать вместо падения "database is locked"
        # - WAL: лучше конкуренция чтение/запись
        # - check_same_thread: обязателен False для async
        _engine = create_async_engine(
            settings.db_url,
            echo=False,
            future=True,
            connect_args={
                "check_same_thread": False,
                "timeout": 30,  # секунды ожидания sqlite
            },
        )
        AsyncSessionLocal.configure(bind=_engine)
    return _engine


async def init_db() -> None:
    engine = get_engine()

    async with engine.begin() as conn:
        # pragma для WAL/таймаутов
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
        await conn.exec_driver_sql("PRAGMA busy_timeout=30000;")  # 30s

        # импорт моделей чтобы create_all увидел таблицы
        from src.infrastructure import db_models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)

        # Лёгкая авто-миграция для существующих sqlite-баз без alembic.
        # Ранее в ui_state не было awaiting_meta_json/history_stack,
        # из-за чего чтение модели падало с "no such column".
        table_info = await conn.exec_driver_sql("PRAGMA table_info('ui_state')")
        existing_columns = {row[1] for row in table_info.fetchall()}

        if "awaiting_meta_json" not in existing_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE ui_state ADD COLUMN awaiting_meta_json TEXT"
            )

        if "history_stack" not in existing_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE ui_state ADD COLUMN history_stack TEXT NOT NULL DEFAULT ''"
            )

        topics_info = await conn.exec_driver_sql("PRAGMA table_info('topics')")
        existing_columns = {row[1] for row in topics_info.fetchall()}

        if "content_json" not in existing_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE topics ADD COLUMN content_json TEXT"
            )

        if "test_json" not in existing_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE topics ADD COLUMN test_json TEXT"
            )

        if "category" not in existing_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE topics ADD COLUMN category TEXT NOT NULL DEFAULT 'Общее'"
            )

        users_info = await conn.exec_driver_sql("PRAGMA table_info('users')")
        user_columns = {row[1] for row in users_info.fetchall()}
        if "username" not in user_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN username TEXT"
            )

        keys_info = await conn.exec_driver_sql("PRAGMA table_info('keys')")
        key_columns = {row[1] for row in keys_info.fetchall()}
        if "key_type" not in key_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE keys ADD COLUMN key_type TEXT NOT NULL DEFAULT 'multi'"
            )
        if "is_disabled" not in key_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE keys ADD COLUMN is_disabled INTEGER NOT NULL DEFAULT 0"
            )
