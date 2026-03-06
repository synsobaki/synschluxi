# src/infrastructure/db_models.py
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db import Base


# =========================
# UI STATE (one-screen)
# =========================
class UIStateRow(Base):
    __tablename__ = "ui_state"

    # 1 строка = 1 пользователь
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    main_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    current_screen: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="menu",
    )

    awaiting_input: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    history_stack: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


# =========================
# USERS
# =========================
class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    active_key: Mapped[str | None] = mapped_column(String(128), nullable=True)

    key_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


# =========================
# LICENSE KEYS
# =========================
class KeyRow(Base):
    __tablename__ = "keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Сам ключ
    value: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )

    # Срок действия (в днях)
    days_valid: Mapped[int] = mapped_column(Integer, nullable=False)

    # Максимальное число активаций
    max_uses: Mapped[int] = mapped_column(Integer, nullable=False)

    # Сколько раз уже активирован
    used_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )