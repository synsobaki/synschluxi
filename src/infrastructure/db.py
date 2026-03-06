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

# Backward-compatible alias used by older imports in the project.
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

        # Lightweight migration for old SQLite databases:
        # add metadata field for awaiting state if it is missing.
        cols = await conn.exec_driver_sql("PRAGMA table_info(ui_state);")
        col_names = {row[1] for row in cols.fetchall()}
        if "awaiting_meta_json" not in col_names:
            await conn.exec_driver_sql(
                "ALTER TABLE ui_state ADD COLUMN awaiting_meta_json TEXT"
            )
