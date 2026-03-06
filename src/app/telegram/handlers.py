from __future__ import annotations

import json
from typing import Any

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import load_settings
from src.infrastructure.repositories.ui_state import UIStateRepo
from src.infrastructure.repositories.keys import KeysRepo
from src.infrastructure.repositories.users import UserRepo
from src.infrastructure.repositories.topics import TopicRepo
from src.services.keygen_service import generate_key
from src.utils.callbacks import unpack

from src.app.telegram.admin_kb import admin_panel_kb, admin_days_kb, admin_uses_kb

router = Router()


def _settings():
    return load_settings()


def _is_admin(user_id: int) -> bool:
    try:
        return int(user_id) == int(_settings().admin_id)
    except Exception:
        return False


async def _safe_render_call(render: Any, method: str, *args, **kwargs):
    fn = getattr(render, method, None)
    if not fn:
        return None
    try:
        return await fn(*args, **kwargs)
    except TypeError:
        return await fn(*args)


@router.message(CommandStart())
async def on_start(message: Message, session: AsyncSession, render: Any):
    user_id = message.from_user.id
    chat_id = message.chat.id
    ui_repo = UIStateRepo(session)
    await ui_repo.get_or_create(user_id)
    await ui_repo.set_awaiting(user_id, None)
    await ui_repo.set_main_message_id(user_id, None)

    if await UserRepo(session).is_active(user_id):
        await _safe_render_call(render, "show_menu", session, chat_id, user_id)
        return

    await _safe_render_call(render, "show_profile", session, chat_id, user_id, first_name=(message.from_user.first_name or ""))


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
    try:
        await cq.answer()
    except Exception:
        pass

    ui_repo = UIStateRepo(session)
    await ui_repo.get_or_create(user_id)

    if data.startswith("adm:"):
        if not _is_admin(user_id):
            return
        if data == "adm:mk:0":
            await cq.message.edit_text("⏳ Выберите срок действия ключа:", reply_markup=admin_days_kb())
            return
        if data == "adm:back:panel":
            await cq.message.edit_text("🔐 Админ-панель", reply_markup=admin_panel_kb())
            return
        if data == "adm:back:days":
            await cq.message.edit_text("⏳ Выберите срок действия ключа:", reply_markup=admin_days_kb())
            return
        if data.startswith("adm:days:"):
            val = data.split(":")[2]
            if val == "custom":
                await ui_repo.set_awaiting(user_id, "admin_days_custom")
                await cq.message.answer("Введи N — срок в днях (1..3650):")
                return
            days = int(val)
            await cq.message.edit_text(f"📅 Срок: <b>{days} дней</b>\n\nВыберите лимит активаций:", reply_markup=admin_uses_kb(days))
            return
        if data.startswith("adm:uses_custom:"):
            days = int(data.split(":")[2])
            await ui_repo.set_awaiting(user_id, "admin_uses_custom", meta={"days": days})
            await cq.message.answer("Введи N — количество активаций (1..10000):")
            return
        if data.startswith("adm:uses:"):
            _, _, days_s, uses_s = data.split(":")
            days, uses = int(days_s), int(uses_s)
            key_value = generate_key()
            await KeysRepo(session).create_key(value=key_value, days_valid=days, max_uses=uses)
            await cq.message.edit_text(
                "✅ <b>Ключ создан</b>\n\n"
                f"<code>{key_value}</code>\n\n📅 Срок: {days} дней\n👥 Активаций: {uses}",
                reply_markup=admin_panel_kb(),
            )
            return
        return

    cb = unpack(data)
    if not cb:
        await _safe_render_call(render, "show_menu", session, chat_id, user_id)
        return

    is_active = await UserRepo(session).is_active(user_id)

    if cb.section == "nav" and cb.action == "menu":
        await _safe_render_call(render, "show_menu", session, chat_id, user_id)
        return
    if cb.section == "nav" and cb.action == "back":
        prev = await ui_repo.pop_history(user_id)
        if prev:
            await _safe_render_call(render, "show_by_screen", session, chat_id, user_id, screen=prev, first_name=(cq.from_user.first_name or ""))
            return
        await _safe_render_call(render, "show_menu", session, chat_id, user_id)
        return

    if cb.section == "menu" and cb.action == "profile":
        await _safe_render_call(render, "show_profile", session, chat_id, user_id, first_name=(cq.from_user.first_name or ""))
        return
    if cb.section == "menu" and cb.action == "archive":
        if not is_active:
            await _safe_render_call(render, "show_profile", session, chat_id, user_id, first_name=(cq.from_user.first_name or ""))
            return
        await _safe_render_call(render, "show_archive", session, chat_id, user_id)
        return
    if cb.section == "menu" and cb.action == "create":
        if not is_active:
            await _safe_render_call(render, "show_profile", session, chat_id, user_id, first_name=(cq.from_user.first_name or ""))
            return
        await _safe_render_call(render, "show_topic_title_input", session, chat_id, user_id)
        return

    if cb.section == "profile" and cb.action == "key_input":
        await _safe_render_call(render, "show_key_input", session, chat_id, user_id)
        return
    if cb.section == "profile" and cb.action == "key_request":
        await _safe_render_call(render, "show_key_request", session, chat_id, user_id)
        return

    if cb.section == "topic" and cb.action == "open":
        await _safe_render_call(render, "show_topic_card", session, chat_id, user_id, topic_id=int(cb.value))
        return
    if cb.section == "topic" and cb.action == "open_last":
        candidate = await TopicRepo(session).get_continue_candidate(user_id)
        if candidate:
            await _safe_render_call(render, "show_topic_card", session, chat_id, user_id, topic_id=candidate.id)
            return
        await _safe_render_call(render, "show_archive", session, chat_id, user_id)
        return
    if cb.section == "topic" and cb.action == "format":
        raw = cb.value.split("|", 1)
        topic_id, fmt = int(raw[0]), raw[1]
        repo = TopicRepo(session)
        topic = await repo.get_by_id(user_id, topic_id)
        if not topic:
            await _safe_render_call(render, "show_archive", session, chat_id, user_id)
            return
        await repo.set_format(user_id, topic_id, fmt)
        await _safe_render_call(render, "show_topic_plan", session, chat_id, user_id, topic_id=topic_id, title=topic.title)
        return
    if cb.section == "topic" and cb.action == "generate":
        await _safe_render_call(render, "show_generation_status", session, chat_id, user_id)
        await _safe_render_call(render, "show_topic_card", session, chat_id, user_id, topic_id=int(cb.value), push_history=False)
        return

    await _safe_render_call(render, "show_menu", session, chat_id, user_id)


@router.message(F.text)
async def on_text(message: Message, session: AsyncSession, render: Any):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = (message.text or "").strip()

    ui_repo = UIStateRepo(session)
    ui = await ui_repo.get_or_create(user_id)

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

        meta = json.loads(ui.awaiting_meta_json or "{}")
        days = int(meta.get("days", 0))
        if days <= 0:
            await ui_repo.set_awaiting(user_id, None)
            await message.answer("Состояние сломано (не выбран срок). Открой /admin заново.")
            return

        key_value = generate_key()
        await KeysRepo(session).create_key(value=key_value, days_valid=days, max_uses=uses)
        await ui_repo.set_awaiting(user_id, None)
        await message.answer(
            "✅ <b>Ключ создан</b>\n\n"
            f"<code>{key_value}</code>\n\n📅 Срок: {days} дней\n👥 Активаций: {uses}",
            reply_markup=admin_panel_kb(),
        )
        return

    if ui.awaiting_input == "key":
        ok = await KeysRepo(session).activate_key(value=text, user_id=user_id)
        if not ok:
            await message.answer("❌ Ключ недействителен, истёк или лимит активаций исчерпан.")
            return
        await ui_repo.set_awaiting(user_id, None)
        await _safe_render_call(render, "show_profile", session, chat_id, user_id, first_name=(message.from_user.first_name or ""))
        return

    if ui.awaiting_input == "topic_title":
        if len(text) < 3:
            await message.answer("Слишком коротко. Напиши тему чуть подробнее 🙂")
            return
        await ui_repo.set_awaiting(user_id, None)
        topic = await TopicRepo(session).create_draft(user_id=user_id, title=text)
        await _safe_render_call(render, "show_format_pick", session, chat_id, user_id, topic_id=topic.id, title=topic.title)
        return
