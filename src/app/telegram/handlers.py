# src/app/telegram/handlers.py
from __future__ import annotations

import json
from typing import Any, Optional

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import load_settings
from src.infrastructure.repositories.ui_state import UIStateRepo
from src.infrastructure.repositories.keys import KeysRepo
from src.services.keygen_service import generate_key

from src.app.telegram.admin_kb import admin_panel_kb, admin_days_kb, admin_uses_kb


# utils.callbacks может быть в твоём проекте (pack/unpack/Act)
# Если нет или сломано — handlers не упадёт: просто не будет понимать такие колбэки.
try:
    from src.utils.callbacks import unpack, Act  # type: ignore
except Exception:  # pragma: no cover
    unpack = None  # type: ignore
    Act = None  # type: ignore


router = Router()


def _settings():
    return load_settings()


def _is_admin(user_id: int) -> bool:
    s = _settings()
    try:
        return int(user_id) == int(s.admin_id)
    except Exception:
        return False


async def _safe_render_call(render: Any, method: str, *args, **kwargs):
    """
    Вызывает render.method(...) если он есть.
    Если сигнатура другая — пробует без kwargs.
    """
    fn = getattr(render, method, None)
    if not fn:
        return None
    try:
        return await fn(*args, **kwargs)
    except TypeError:
        return await fn(*args)


def _cb_act_name(cb: Any) -> str:
    """
    Приводим cb.act к строке, чтобы не зависеть от enum/типа.
    """
    a = getattr(cb, "act", None)
    if a is None:
        return ""
    # enum?
    if hasattr(a, "name"):
        return str(a.name)
    return str(a)


def _simple_act_from_data(data: str) -> str:
    """
    На случай если в callback_data просто строки типа:
    menu / profile / archive / create / back / home
    """
    d = (data or "").strip().lower()
    return d


@router.message(CommandStart())
async def on_start(message: Message, session: AsyncSession, render: Any):
    user_id = message.from_user.id
    chat_id = message.chat.id

    ui_repo = UIStateRepo(session)
    await ui_repo.get_or_create(user_id)
    await ui_repo.set_awaiting(user_id, None)

    # показываем главное меню one-screen
    await _safe_render_call(render, "show_menu", session, chat_id, user_id)


@router.message(Command("admin"))
async def on_admin(message: Message, session: AsyncSession):
    if not _is_admin(message.from_user.id):
        return
    await message.answer("🔐 Админ-панель", reply_markup=admin_panel_kb())


@router.callback_query()
async def on_any_callback(cq: CallbackQuery, session: AsyncSession, render: Any):
    user_id = cq.from_user.id
    chat_id = cq.message.chat.id if cq.message else user_id
    data = cq.data or ""

    # важно: отвечаем сразу, чтобы кнопки не "думали"
    try:
        await cq.answer()
    except Exception:
        pass

    ui_repo = UIStateRepo(session)
    await ui_repo.get_or_create(user_id)

    # ---------------------------
    # ADMIN FLOW (adm:*)
    # ---------------------------
    if data.startswith("adm:"):
        if not _is_admin(user_id):
            return

        # adm:mk:0 -> выбор срока
        if data == "adm:mk:0":
            await cq.message.edit_text("⏳ Выберите срок действия ключа:", reply_markup=admin_days_kb())
            return

        # back
        if data == "adm:back:panel":
            await cq.message.edit_text("🔐 Админ-панель", reply_markup=admin_panel_kb())
            return

        if data == "adm:back:days":
            await cq.message.edit_text("⏳ Выберите срок действия ключа:", reply_markup=admin_days_kb())
            return

        # days
        if data.startswith("adm:days:"):
            val = data.split(":")[2]
            if val == "custom":
                await ui_repo.set_awaiting(user_id, "admin_days_custom")
                await cq.message.answer("Введи N — срок в днях (1..3650):")
                return

            days = int(val)
            await cq.message.edit_text(
                f"📅 Срок: <b>{days} дней</b>\n\nВыберите лимит активаций:",
                reply_markup=admin_uses_kb(days),
            )
            return

        # uses custom
        if data.startswith("adm:uses_custom:"):
            days = int(data.split(":")[2])
            await ui_repo.set_awaiting(user_id, "admin_uses_custom", meta={"days": days})
            await cq.message.answer("Введи N — количество активаций (1..10000):")
            return

        # uses fixed
        if data.startswith("adm:uses:"):
            _, _, days_s, uses_s = data.split(":")
            days = int(days_s)
            uses = int(uses_s)

            key_value = generate_key()
            await KeysRepo(session).create_key(key=key_value, days_valid=days, max_uses=uses)

            await cq.message.edit_text(
                "✅ <b>Ключ создан</b>\n\n"
                f"<code>{key_value}</code>\n\n"
                f"📅 Срок: {days} дней\n"
                f"👥 Активаций: {uses}",
                reply_markup=admin_panel_kb(),
            )
            return

        return

    # ---------------------------
    # APP CALLBACKS (твоя схема через unpack/Act)
    # ---------------------------
    cb = None
    if unpack is not None:
        try:
            cb = unpack(data)
        except Exception:
            cb = None

    if cb is not None:
        act = _cb_act_name(cb)

        # Поддержка самых частых действий.
        # Если твой Act называется иначе — всё равно не упадёт, просто не матчнется.
        if act in ("MENU", "HOME"):
            await _safe_render_call(render, "show_menu", session, chat_id, user_id)
            return

        if act in ("PROFILE",):
            await _safe_render_call(
                render,
                "show_profile",
                session,
                chat_id,
                user_id,
                first_name=(cq.from_user.first_name or ""),
            )
            return

        if act in ("ARCHIVE",):
            await _safe_render_call(render, "show_archive", session, chat_id, user_id)
            return

        if act in ("CREATE", "CREATE_NOTE", "CREATE_SUMMARY", "NEW_TOPIC"):
            # если у тебя первый шаг — запросить тему текстом:
            await ui_repo.set_awaiting(user_id, "topic_title")
            await cq.message.answer("Напиши тему для конспекта (например: «Интерфейсы в Java»):")
            return

        if act in ("KEY_INPUT", "ENTER_KEY"):
            await _safe_render_call(render, "show_key_input", session, chat_id, user_id)
            return

        if act in ("KEY_REQUEST", "REQUEST_KEY"):
            await _safe_render_call(render, "show_key_request", session, chat_id, user_id)
            return

        if act in ("BACK",):
            prev = await ui_repo.pop_history(user_id)
            if prev:
                # если у тебя есть универсальный show_by_screen
                r = await _safe_render_call(
                    render,
                    "show_by_screen",
                    session,
                    chat_id,
                    user_id,
                    screen=prev,
                    first_name=(cq.from_user.first_name or ""),
                )
                if r is not None:
                    return
            # fallback
            await _safe_render_call(render, "show_menu", session, chat_id, user_id)
            return

        # если не распознали act — fallback в меню
        await _safe_render_call(render, "show_menu", session, chat_id, user_id)
        return

    # ---------------------------
    # FALLBACK: простые строковые колбэки
    # ---------------------------
    simp = _simple_act_from_data(data)
    if simp in ("menu", "home"):
        await _safe_render_call(render, "show_menu", session, chat_id, user_id)
        return
    if simp == "profile":
        await _safe_render_call(render, "show_profile", session, chat_id, user_id, first_name=(cq.from_user.first_name or ""))
        return
    if simp == "archive":
        await _safe_render_call(render, "show_archive", session, chat_id, user_id)
        return

    # совсем ничего не поняли — не ломаем UX, просто меню
    await _safe_render_call(render, "show_menu", session, chat_id, user_id)


@router.message(F.text)
async def on_text(message: Message, session: AsyncSession, render: Any):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = (message.text or "").strip()

    ui_repo = UIStateRepo(session)
    ui = await ui_repo.get_or_create(user_id)

    # ---------------------------
    # ADMIN: custom days
    # ---------------------------
    if ui.awaiting_input == "admin_days_custom":
        if not _is_admin(user_id):
            await ui_repo.set_awaiting(user_id, None)
            return

        try:
            days = int(text)
            if days < 1 or days > 3650:
                raise ValueError
        except Exception:
            await message.answer("Введи число дней (1..3650).")
            return

        await ui_repo.set_awaiting(user_id, None)
        await message.answer(f"📅 Срок: {days} дней\nВыбери лимит активаций:", reply_markup=admin_uses_kb(days))
        return

    # ---------------------------
    # ADMIN: custom uses
    # ---------------------------
    if ui.awaiting_input == "admin_uses_custom":
        if not _is_admin(user_id):
            await ui_repo.set_awaiting(user_id, None)
            return

        try:
            uses = int(text)
            if uses < 1 or uses > 10000:
                raise ValueError
        except Exception:
            await message.answer("Введи число активаций (1..10000).")
            return

        try:
            meta = json.loads(ui.awaiting_meta_json or "{}")
            if not isinstance(meta, dict):
                meta = {}
        except Exception:
            meta = {}

        days = int(meta.get("days", 0))
        if days <= 0:
            await ui_repo.set_awaiting(user_id, None)
            await message.answer("Состояние сломано (не выбран срок). Открой /admin заново.")
            return

        key_value = generate_key()
        await KeysRepo(session).create_key(key=key_value, days_valid=days, max_uses=uses)

        await ui_repo.set_awaiting(user_id, None)
        await message.answer(
            "✅ <b>Ключ создан</b>\n\n"
            f"<code>{key_value}</code>\n\n"
            f"📅 Срок: {days} дней\n"
            f"👥 Активаций: {uses}",
            reply_markup=admin_panel_kb(),
        )
        return

    # ---------------------------
    # USER: ввод ключа (если у тебя так устроено)
    # ---------------------------
    if ui.awaiting_input == "key":
        # KeysRepo.activate_key должен существовать в твоём репозитории.
        # Если у тебя метод называется иначе — скажи, я подгоню.
        ok = False
        try:
            ok = await KeysRepo(session).activate_key(key=text, user_id=user_id)
        except Exception:
            ok = False

        if not ok:
            await message.answer("❌ Ключ недействителен, истёк или лимит активаций исчерпан.")
            return

        await ui_repo.set_awaiting(user_id, None)
        await _safe_render_call(render, "show_profile", session, chat_id, user_id, first_name=(message.from_user.first_name or ""))
        return

    # ---------------------------
    # USER: ввод темы (первый шаг создания)
    # ---------------------------
    if ui.awaiting_input == "topic_title":
        title = text
        if len(title) < 3:
            await message.answer("Слишком коротко. Напиши тему чуть подробнее 🙂")
            return

        # дальше у тебя будет создание draft topic в TopicRepo и показ выбора формата.
        # чтобы сейчас не ломать проект, просто сбрасываем ожидание и кидаем в меню/или формат пик.
        await ui_repo.set_awaiting(user_id, None)

        # если у тебя есть show_format_pick — отлично, используем
        r = await _safe_render_call(render, "show_format_pick", session, chat_id, user_id, title=title)
        if r is not None:
            return

        await message.answer(f"✅ Тема принята: <b>{title}</b>\n(Дальше подключим создание draft + формат)")
        await _safe_render_call(render, "show_menu", session, chat_id, user_id)
        return

    # ---------------------------
    # default: не ломаем UX — просто меню one-screen
    # ---------------------------
    await _safe_render_call(render, "show_menu", session, chat_id, user_id)