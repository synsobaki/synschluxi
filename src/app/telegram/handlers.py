from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import load_settings
from src.infrastructure.repositories.ui_state import UIStateRepo
from src.infrastructure.repositories.keys import KeysRepo
from src.infrastructure.repositories.users import UserRepo
from src.infrastructure.repositories.topics import TopicRepo
from src.services.keygen_service import generate_key
from src.services.pdf_service import PDFService
from src.services.rag import RAGService
from src.services.text_extract import TextExtractService
from src.services.summary_service import SummaryService, SummarySource
from src.services.test_service import TestService
from src.services.access_notifications import notify_access_change
from src.utils.callbacks import unpack

from src.app.telegram.admin_kb import (
    admin_panel_kb,
    admin_days_kb,
    admin_uses_kb,
    admin_keys_menu_kb,
    admin_users_menu_kb,
    admin_key_types_kb,
    admin_key_card_kb,
    admin_user_card_kb,
)

router = Router()


def _settings():
    return load_settings()


def _is_admin(user_id: int) -> bool:
    try:
        return int(user_id) == int(_settings().admin_id)
    except Exception:
        return False




def _fmt_dt(dt) -> str:
    return dt.strftime("%d.%m.%Y %H:%M") if dt else "—"


def _key_type_label(key_type: str) -> str:
    return {
        "single": "одноразовый",
        "multi": "мультиактивация",
        "lifetime": "бессрочный",
    }.get(key_type, key_type)


async def _render_key_card(session: AsyncSession, message: Message, key_id: int):
    repo = KeysRepo(session)
    key = await repo.get_by_id(key_id)
    if not key:
        await message.answer("Ключ не найден.")
        return
    activations = await repo.list_activations(key_id)
    users_lines = []
    for activation, user in activations[:10]:
        users_lines.append(
            f"• {activation.user_id} | @{getattr(user, 'username', '-') or '-'} | {_fmt_dt(activation.activated_at)}"
        )
    users_block = "\n".join(users_lines) if users_lines else "Нет активаций"
    text = (
        f"🔑 Карточка ключа\n\n"
        f"Ключ: <code>{key.value}</code>\n"
        f"Тип: {_key_type_label(key.key_type)}\n"
        f"Срок действия: {key.days_valid if key.days_valid else 'бессрочно'}\n"
        f"Лимит активаций: {key.max_uses}\n"
        f"Использовано: {key.used_count}\n"
        f"Статус: {repo.key_status(key)}\n\n"
        f"Пользователи:\n{users_block}"
    )
    await message.answer(text, reply_markup=admin_key_card_kb(key_id))


async def _render_user_card(session: AsyncSession, message: Message, user_id: int):
    user = await UserRepo(session).get_or_create(user_id)
    topics = await TopicRepo(session).list_recent(user_id, limit=100)
    avg = int(sum(t.mastery for t in topics) / len(topics)) if topics else 0
    text = (
        "👤 Карточка пользователя\n\n"
        f"telegram id: {user.id}\n"
        f"имя: {user.first_name or '-'}\n"
        f"username: @{user.username or '-'}\n"
        f"дата регистрации: {_fmt_dt(user.created_at)}\n"
        f"активный ключ: {user.active_key or 'нет'}\n"
        f"срок доступа: {_fmt_dt(user.key_expires_at)}\n"
        f"количество созданных тем: {len(topics)}\n"
        f"средний прогресс обучения: {avg}%"
    )
    await message.answer(text, reply_markup=admin_user_card_kb(user_id))


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
    await UserRepo(session).get_or_create(user_id, first_name=message.from_user.first_name, username=message.from_user.username)
    await ui_repo.set_awaiting(user_id, None)
    await ui_repo.set_main_message_id(user_id, None)

    if await UserRepo(session).is_active(user_id):
        await _safe_render_call(render, "show_menu", session, chat_id, user_id)
        return

    await _safe_render_call(render, "show_access_gate", session, chat_id, user_id)


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

    if data.startswith("notify:close"):
        try:
            await cq.message.delete()
        except Exception:
            pass
        return

    if data.startswith("adm:"):
        if not _is_admin(user_id):
            return
        repo = KeysRepo(session)
        user_repo = UserRepo(session)

        if data == "adm:back:panel":
            await cq.message.edit_text("🔐 Админ-панель", reply_markup=admin_panel_kb())
            return
        if data == "adm:keys:menu":
            await cq.message.edit_text("🔑 Управление ключами", reply_markup=admin_keys_menu_kb())
            return
        if data == "adm:users:menu":
            await cq.message.edit_text("👤 Управление пользователями", reply_markup=admin_users_menu_kb())
            return
        if data == "adm:stats:menu":
            keys = await repo.list_keys(limit=500)
            users = await user_repo.list_users(limit=500)
            await cq.message.edit_text(f"📊 Статистика\n\nКлючей: {len(keys)}\nПользователей: {len(users)}", reply_markup=admin_panel_kb())
            return

        if data == "adm:key:create":
            await cq.message.edit_text("Выберите тип ключа:", reply_markup=admin_key_types_kb())
            return
        if data.startswith("adm:type:"):
            key_type = data.split(":")[2]
            if key_type == "lifetime":
                await ui_repo.set_awaiting(user_id, "admin_create_lifetime_uses")
                await cq.message.answer("Введите количество активаций для бессрочного ключа (1..10000):")
                return
            await ui_repo.set_awaiting(user_id, "admin_key_type", meta={"key_type": key_type})
            await cq.message.edit_text("⏳ Выберите срок действия ключа:", reply_markup=admin_days_kb())
            return

        if data == "adm:key:list":
            keys = await repo.list_keys(limit=30)
            if not keys:
                await cq.message.answer("Ключей пока нет.")
                return
            lines = ["🔑 Список ключей:"]
            for row in keys:
                lines.append(
                    f"#{row.id} <code>{row.value}</code> | срок: {row.days_valid if row.days_valid else '∞'} | "
                    f"{row.used_count}/{row.max_uses} | {repo.key_status(row)}"
                )
            await cq.message.answer("\n".join(lines))
            await cq.message.answer("Введите ID ключа, чтобы открыть карточку.")
            await ui_repo.set_awaiting(user_id, "admin_open_key")
            return

        if data == "adm:key:find":
            await ui_repo.set_awaiting(user_id, "admin_find_key")
            await cq.message.answer("Введите ключ в формате UMK-XXXX-XXXX")
            return

        if data.startswith("adm:keycard:"):
            key_id = int(data.split(":")[2])
            await _render_key_card(session, cq.message, key_id)
            return

        if data.startswith("adm:grant:"):
            key_id = int(data.split(":")[2])
            await ui_repo.set_awaiting(user_id, "admin_grant_key", meta={"key_id": key_id})
            await cq.message.answer("Введите telegram user_id или username для выдачи ключа:")
            return

        if data.startswith("adm:editdays:"):
            key_id = int(data.split(":")[2])
            await ui_repo.set_awaiting(user_id, "admin_edit_days", meta={"key_id": key_id})
            await cq.message.answer("Введите новый срок действия в днях (0 = бессрочно):")
            return

        if data.startswith("adm:edituses:"):
            key_id = int(data.split(":")[2])
            await ui_repo.set_awaiting(user_id, "admin_edit_uses", meta={"key_id": key_id})
            await cq.message.answer("Введите новый лимит активаций:")
            return

        if data.startswith("adm:extend:"):
            key_id = int(data.split(":")[2])
            await ui_repo.set_awaiting(user_id, "admin_extend_access", meta={"key_id": key_id})
            await cq.message.answer("Введите user_id/username и дни через пробел (пример: 12345 30):")
            return

        if data.startswith("adm:toggle:"):
            key_id = int(data.split(":")[2])
            key = await repo.get_by_id(key_id)
            if not key:
                await cq.message.answer("Ключ не найден")
                return
            updated = await repo.update_key(key_id, disable=not bool(key.is_disabled))
            await cq.message.answer(f"Статус ключа: {'отключён' if updated and updated.is_disabled else 'активен'}")
            if updated:
                acts = await repo.list_activations(key_id)
                for a, _ in acts:
                    await notify_access_change(cq.bot, a.user_id, title="Доступ обновлён", body="Администратор изменил параметры вашего доступа.")
            return

        if data.startswith("adm:delete:"):
            key_id = int(data.split(":")[2])
            ok, _, users = await repo.delete_key(key_id)
            if not ok:
                await cq.message.answer("Ключ не найден")
                return
            for uid in users:
                await notify_access_change(
                    cq.bot,
                    uid,
                    icon="⚠️",
                    title="Доступ изменён",
                    body="Ваш лицензионный ключ был деактивирован администратором.",
                )
            await cq.message.answer("Ключ удалён. Пользовательские доступы отключены.")
            return

        if data == "adm:user:find":
            await ui_repo.set_awaiting(user_id, "admin_find_user")
            await cq.message.answer("Введите user_id или username:")
            return

        if data == "adm:user:list":
            users = await user_repo.list_users(limit=30)
            if not users:
                await cq.message.answer("Пользователей пока нет.")
                return
            lines = ["👤 Пользователи:"]
            for u in users:
                lines.append(f"• {u.id} | @{u.username or '-'} | ключ: {u.active_key or 'нет'}")
            await cq.message.answer("\n".join(lines))
            await cq.message.answer("Введите user_id для карточки пользователя.")
            await ui_repo.set_awaiting(user_id, "admin_open_user")
            return

        if data.startswith("adm:userextend:"):
            target_user_id = int(data.split(":")[2])
            await ui_repo.set_awaiting(user_id, "admin_extend_user_direct", meta={"target_user_id": target_user_id})
            await cq.message.answer("На сколько дней продлить доступ?")
            return

        if data.startswith("adm:useroff:"):
            target_user_id = int(data.split(":")[2])
            await user_repo.clear_active(target_user_id)
            await notify_access_change(cq.bot, target_user_id, icon="⚠️", title="Доступ изменён", body="Администратор отключил ваш доступ.")
            await cq.message.answer("Доступ пользователя отключен.")
            return

        if data.startswith("adm:userdelkey:"):
            target_user_id = int(data.split(":")[2])
            await user_repo.clear_active(target_user_id)
            await notify_access_change(cq.bot, target_user_id, icon="⚠️", title="Доступ изменён", body="Ваш лицензионный ключ был удалён администратором.")
            await cq.message.answer("Ключ у пользователя удалён.")
            return

        if data.startswith("adm:usertopics:"):
            target_user_id = int(data.split(":")[2])
            topics = await TopicRepo(session).list_recent(target_user_id, limit=20)
            if not topics:
                await cq.message.answer("У пользователя нет тем.")
                return
            await cq.message.answer("\n".join([f"• {t.title} ({t.mastery}%)" for t in topics]))
            return

        if data.startswith("adm:usergrant:"):
            target_user_id = int(data.split(":")[2])
            await ui_repo.set_awaiting(user_id, "admin_user_grant_direct", meta={"target_user_id": target_user_id})
            await cq.message.answer("Введите ID ключа для выдачи пользователю:")
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
            state = await ui_repo.get_or_create(user_id)
            meta = json.loads(state.awaiting_meta_json or "{}")
            key_type = meta.get("key_type", "multi")
            await ui_repo.set_awaiting(user_id, "admin_uses_custom", meta={"days": days, "key_type": key_type})
            await cq.message.answer("Введи N — количество активаций (1..10000):")
            return
        if data.startswith("adm:uses:"):
            _, _, days_s, uses_s = data.split(":")
            days, uses = int(days_s), int(uses_s)
            state = await ui_repo.get_or_create(user_id)
            meta = json.loads(state.awaiting_meta_json or "{}")
            key_type = meta.get("key_type", "multi")
            key_value = generate_key()
            if key_type == "lifetime":
                days = 0
            created = await repo.create_key(value=key_value, days_valid=days, max_uses=uses, key_type=key_type)
            await cq.message.edit_text(
                "✅ <b>Ключ создан</b>\n\n"
                f"ID: {created.id}\n<code>{key_value}</code>\n\n"
                f"Тип: {_key_type_label(key_type)}\n📅 Срок: {days if days else 'бессрочно'}\n👥 Активаций: {uses}",
                reply_markup=admin_keys_menu_kb(),
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
    if cb.section == "menu" and cb.action == "works":
        if not is_active:
            return await _safe_render_call(render, "show_key_input", session, chat_id, user_id)
        await _safe_render_call(render, "show_works_list", session, chat_id, user_id, page=0)
        return
    if cb.section == "menu" and cb.action == "create":
        if not is_active:
            return await _safe_render_call(render, "show_key_input", session, chat_id, user_id)
        await _safe_render_call(render, "show_topic_input", session, chat_id, user_id)
        return
    if cb.section == "menu" and cb.action == "file":
        if not is_active:
            return await _safe_render_call(render, "show_key_input", session, chat_id, user_id)
        await _safe_render_call(render, "show_file_upload", session, chat_id, user_id)
        return

    if cb.section == "works" and cb.action == "page":
        await _safe_render_call(render, "show_works_list", session, chat_id, user_id, page=max(int(cb.value), 0), push_history=False)
        return

    if cb.section == "profile" and cb.action == "key_input":
        await _safe_render_call(render, "show_key_input", session, chat_id, user_id)
        return
    if cb.section == "profile" and cb.action == "key_request":
        await _safe_render_call(render, "show_request_key", session, chat_id, user_id)
        return

    if cb.section == "works" and cb.action == "open":
        await _safe_render_call(render, "show_topic_card", session, chat_id, user_id, topic_id=int(cb.value))
        return

    if cb.section == "topic" and cb.action == "open":
        await _safe_render_call(render, "show_topic_card", session, chat_id, user_id, topic_id=int(cb.value))
        return
    if cb.section == "topic" and cb.action == "open_last":
        candidate = await TopicRepo(session).get_continue_candidate(user_id)
        if candidate:
            await _safe_render_call(render, "show_topic_card", session, chat_id, user_id, topic_id=candidate.id)
            return
        await _safe_render_call(render, "show_works_list", session, chat_id, user_id)
        return
    if cb.section == "topic" and cb.action == "section":
        topic_id, idx = map(int, cb.value.split("|", 1))
        await _safe_render_call(render, "show_topic_card", session, chat_id, user_id, topic_id=topic_id, section_idx=idx, push_history=False)
        return
    if cb.section == "topic" and cb.action == "format":
        topic_id, fmt = cb.value.split("|", 1)
        topic_id = int(topic_id)
        repo = TopicRepo(session)
        topic = await repo.get_by_id(user_id, topic_id)
        if not topic:
            return await _safe_render_call(render, "show_works_list", session, chat_id, user_id)
        await repo.set_format(user_id, topic_id, fmt)
        plan = SummaryService().build_plan(SummarySource(title=topic.title, source_type=topic.source_type or "topic"), fmt)
        await _safe_render_call(render, "show_plan_preview", session, chat_id, user_id, topic_id=topic_id, title=topic.title, plan=plan)
        return
    if cb.section == "topic" and cb.action == "generate":
        topic_id = int(cb.value)
        repo = TopicRepo(session)
        topic = await repo.get_by_id(user_id, topic_id)
        if not topic:
            return await _safe_render_call(render, "show_works_list", session, chat_id, user_id)
        for step in range(4):
            await _safe_render_call(render, "show_generation_status", session, chat_id, user_id, step=step, push_history=(step == 0))
        summary_service = SummaryService()
        test_service = TestService()
        source_text = ""
        ui_state = await ui_repo.get_or_create(user_id)
        meta = json.loads(ui_state.awaiting_meta_json or "{}")
        if ui_state.awaiting_input == "topic_file_mode" and int(meta.get("topic_id", 0)) == topic_id:
            source_text = str(meta.get("source_text", ""))
            await ui_repo.set_awaiting(user_id, None)
        source = SummarySource(title=topic.title, source_type=topic.source_type or "topic", source_text=source_text, file_name=topic.source_file_name)
        summary_text, sections = summary_service.generate_summary(source, topic.fmt or "brief")
        test = test_service.generate_test_from_summary(sections)
        await repo.save_generated_material(user_id=user_id, topic_id=topic_id, content_sections=sections, test_questions=test, summary_text=summary_text)
        await _safe_render_call(render, "show_topic_card", session, chat_id, user_id, topic_id=topic_id, push_history=False)
        return
    if cb.section == "topic" and cb.action == "edit":
        await _safe_render_call(render, "show_topic_edit", session, chat_id, user_id, topic_id=int(cb.value))
        return
    if cb.section == "topic" and cb.action == "improve":
        topic_id, mode = cb.value.split("|", 1)
        topic_id = int(topic_id)
        repo = TopicRepo(session)
        topic = await repo.get_by_id(user_id, topic_id)
        if not topic:
            return await _safe_render_call(render, "show_works_list", session, chat_id, user_id)
        sections = SummaryService().rewrite_summary(repo.get_topic_sections(topic), mode)
        await repo.save_generated_material(user_id=user_id, topic_id=topic_id, content_sections=sections, test_questions=repo.get_topic_test(topic), summary_text=topic.summary_text)
        await _safe_render_call(render, "show_topic_card", session, chat_id, user_id, topic_id=topic_id, push_history=False)
        return
    if cb.section == "topic" and cb.action == "pdf":
        topic_id = int(cb.value)
        topic = await TopicRepo(session).get_by_id(user_id, topic_id)
        if not topic:
            return await _safe_render_call(render, "show_works_list", session, chat_id, user_id)
        sections = TopicRepo(session).get_topic_sections(topic)
        data = PDFService().export_summary_pdf(topic.title, topic.fmt or "brief", sections)
        await cq.message.answer_document(BufferedInputFile(data, filename=f"{topic.title[:30]}.pdf"))
        return

    if cb.section == "test" and cb.action == "start":
        topic_id = int(cb.value)
        await ui_repo.set_awaiting(user_id, "test", meta={"topic_id": topic_id, "q_idx": 0, "score": 0, "weak": "Ключевые понятия"})
        await _safe_render_call(render, "show_test_question", session, chat_id, user_id, topic_id=topic_id, q_idx=0)
        return

    if cb.section == "test" and cb.action == "answer":
        topic_id, q_idx, answer_idx = map(int, cb.value.split("|", 2))
        topic = await TopicRepo(session).get_by_id(user_id, topic_id)
        if not topic:
            return await _safe_render_call(render, "show_works_list", session, chat_id, user_id)

        test = TopicRepo(session).get_topic_test(topic)
        if not test:
            return await _safe_render_call(render, "show_topic_card", session, chat_id, user_id, topic_id=topic_id)

        state = await ui_repo.get_or_create(user_id)
        meta = json.loads(state.awaiting_meta_json or "{}")
        score = int(meta.get("score", 0))

        question = test[q_idx]
        correct = int(question.get("correct", -1)) == answer_idx
        if correct:
            score += 1
        await cq.answer("Верно!" if correct else "Есть ошибка")

        next_idx = q_idx + 1
        weak = str(question.get("section", "Ключевые понятия")) if not correct else str(meta.get("weak", "Ключевые понятия"))
        if next_idx >= len(test):
            mastery = min(100, max(40, int(score * 100 / len(test))))
            status = "mastered" if mastery >= 80 else "ready"
            await TopicRepo(session).set_status(user_id, topic_id, status=status, mastery=mastery)
            await ui_repo.set_awaiting(user_id, None)
            weak_sections = [weak] if weak else []
            await TopicRepo(session).set_test_feedback(user_id, topic_id, {"score": score, "total": len(test)}, weak)
            await _safe_render_call(render, "show_test_result", session, chat_id, user_id, topic_id=topic_id, score=score, total=len(test), weak_sections=weak_sections)
            await ui_repo.set_awaiting(user_id, "weak_training", meta={"topic_id": topic_id, "weak": weak})
            return

        await ui_repo.set_awaiting(user_id, "test", meta={"topic_id": topic_id, "q_idx": next_idx, "score": score, "weak": weak})
        await _safe_render_call(render, "show_test_question", session, chat_id, user_id, topic_id=topic_id, q_idx=next_idx, push_history=False)
        return

    if cb.section == "training" and cb.action == "open":
        topic_id = int(str(cb.value).split("|", 1)[0])
        ui = await ui_repo.get_or_create(user_id)
        meta = json.loads(ui.awaiting_meta_json or "{}")
        weak = str(meta.get("weak", "Ключевые понятия"))
        topic = await TopicRepo(session).get_by_id(user_id, topic_id)
        if not topic:
            return
        sections = TopicRepo(session).get_topic_sections(topic)
        weak_section = next((s for s in sections if s.get("title") == weak), sections[0] if sections else {"title": weak, "body": ""})
        test = TopicRepo(session).get_topic_test(topic)
        wrong_answers = [q for q in test if str(q.get("section_title") or q.get("section")) == weak]
        training_text = TestService().build_training_from_weak_section(topic.title, weak_section, wrong_answers)
        await _safe_render_call(render, "show_weak_section_training", session, chat_id, user_id, topic_id=topic_id, weak_section=weak, training_text=training_text)
        return

    await _safe_render_call(render, "show_menu", session, chat_id, user_id)


@router.message(F.document)
async def on_document(message: Message, session: AsyncSession, render: Any):
    user_id = message.from_user.id
    chat_id = message.chat.id
    ui_repo = UIStateRepo(session)
    ui = await ui_repo.get_or_create(user_id)
    if ui.awaiting_input != "file_upload":
        return

    doc = message.document
    suffix = Path(doc.file_name or "").suffix.lower()
    if suffix not in {".txt", ".pdf", ".docx"}:
        await message.answer("Поддерживаются только txt, pdf, docx")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        await message.bot.download(doc, destination=tmp)
        path = tmp.name

    try:
        extracted = await TextExtractService().extract_text(path, doc.file_name)
    except Exception as e:
        await message.answer(f"Не удалось обработать файл: {e}")
        return
    finally:
        Path(path).unlink(missing_ok=True)

    topic = await TopicRepo(session).create_draft(user_id=user_id, title=Path(doc.file_name or "Документ").stem, source_type="file", source_file_name=doc.file_name)
    await ui_repo.set_awaiting(user_id, None)
    await ui_repo.set_awaiting(user_id, "topic_file_mode", meta={"topic_id": topic.id, "source_text": extracted})
    await _safe_render_call(render, "show_format_pick", session, chat_id, user_id, topic_id=topic.id, title=topic.title)


@router.message(F.text)
async def on_text(message: Message, session: AsyncSession, render: Any):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = (message.text or "").strip()

    ui_repo = UIStateRepo(session)
    ui = await ui_repo.get_or_create(user_id)

    if ui.awaiting_input and ui.awaiting_input.startswith("admin"):
        if not _is_admin(user_id):
            await ui_repo.set_awaiting(user_id, None)
            return

        repo = KeysRepo(session)
        user_repo = UserRepo(session)
        meta = json.loads(ui.awaiting_meta_json or "{}")

        if ui.awaiting_input == "admin_days_custom":
            try:
                days = int(text)
                if days < 1 or days > 3650:
                    raise ValueError
            except Exception:
                await message.answer("Введи число дней (1..3650).")
                return
            key_type = meta.get("key_type", "multi")
            await ui_repo.set_awaiting(user_id, None)
            await message.answer(f"📅 Срок: {days} дней\nВыбери лимит активаций:", reply_markup=admin_uses_kb(days))
            await ui_repo.set_awaiting(user_id, "admin_key_type", meta={"key_type": key_type})
            return

        if ui.awaiting_input == "admin_create_lifetime_uses":
            try:
                uses = int(text)
                if uses < 1 or uses > 10000:
                    raise ValueError
            except Exception:
                await message.answer("Введи число активаций (1..10000).")
                return
            key_value = generate_key()
            created = await repo.create_key(value=key_value, days_valid=0, max_uses=uses, key_type="lifetime")
            await ui_repo.set_awaiting(user_id, None)
            await message.answer(f"✅ Ключ создан\nID: {created.id}\n<code>{created.value}</code>", reply_markup=admin_keys_menu_kb())
            return

        if ui.awaiting_input == "admin_uses_custom":
            try:
                uses = int(text)
                if uses < 1 or uses > 10000:
                    raise ValueError
            except Exception:
                await message.answer("Введи число активаций (1..10000).")
                return
            days = int(meta.get("days", 0))
            key_type = meta.get("key_type", "multi")
            if days <= 0 and key_type != "lifetime":
                await ui_repo.set_awaiting(user_id, None)
                await message.answer("Состояние сломано (не выбран срок). Открой /admin заново.")
                return
            if key_type == "lifetime":
                days = 0
            key_value = generate_key()
            created = await repo.create_key(value=key_value, days_valid=days, max_uses=uses, key_type=key_type)
            await ui_repo.set_awaiting(user_id, None)
            await message.answer(
                "✅ <b>Ключ создан</b>\n\n"
                f"ID: {created.id}\n<code>{key_value}</code>\n\n📅 Срок: {days if days else 'бессрочно'} дней\n👥 Активаций: {uses}",
                reply_markup=admin_keys_menu_kb(),
            )
            return

        if ui.awaiting_input == "admin_open_key":
            if not text.isdigit():
                await message.answer("Введите числовой ID ключа.")
                return
            await _render_key_card(session, message, int(text))
            await ui_repo.set_awaiting(user_id, None)
            return

        if ui.awaiting_input == "admin_find_key":
            key = await repo.get_by_key(text)
            await ui_repo.set_awaiting(user_id, None)
            if not key:
                await message.answer("Ключ не найден.")
                return
            await _render_key_card(session, message, key.id)
            return

        if ui.awaiting_input == "admin_grant_key":
            target = await user_repo.find_by_identity(text)
            if not target:
                await message.answer("Пользователь не найден. Пользователь должен хотя бы раз запустить бота.")
                return
            key_id = int(meta.get("key_id", 0))
            ok, key = await repo.grant_key_to_user(key_id, target.id)
            await ui_repo.set_awaiting(user_id, None)
            if not ok or not key:
                await message.answer("Не удалось выдать ключ (исчерпан, отключен или не найден).")
                return
            await message.answer(f"Ключ <code>{key.value}</code> выдан пользователю {target.id}.")
            await notify_access_change(message.bot, target.id, title="Доступ обновлён", body="Администратор выдал вам лицензионный ключ.")
            return

        if ui.awaiting_input == "admin_edit_days":
            try:
                days = int(text)
                if days < 0 or days > 3650:
                    raise ValueError
            except Exception:
                await message.answer("Введите срок 0..3650")
                return
            key_id = int(meta.get("key_id", 0))
            key = await repo.update_key(key_id, days_valid=days)
            await ui_repo.set_awaiting(user_id, None)
            if not key:
                await message.answer("Ключ не найден")
                return
            acts = await repo.list_activations(key_id)
            for a, _ in acts:
                await notify_access_change(message.bot, a.user_id, title="Доступ обновлён", body="Администратор изменил параметры вашего доступа.")
            await message.answer("Параметры ключа обновлены.")
            return

        if ui.awaiting_input == "admin_edit_uses":
            try:
                uses = int(text)
                if uses < 1 or uses > 10000:
                    raise ValueError
            except Exception:
                await message.answer("Введите лимит 1..10000")
                return
            key_id = int(meta.get("key_id", 0))
            key = await repo.update_key(key_id, max_uses=uses)
            await ui_repo.set_awaiting(user_id, None)
            if not key:
                await message.answer("Ключ не найден")
                return
            acts = await repo.list_activations(key_id)
            for a, _ in acts:
                await notify_access_change(message.bot, a.user_id, title="Доступ обновлён", body="Администратор изменил параметры вашего доступа.")
            await message.answer("Лимит активаций обновлен.")
            return

        if ui.awaiting_input == "admin_extend_access":
            parts = text.split()
            if len(parts) != 2:
                await message.answer("Формат: user_id/username дни")
                return
            target = await user_repo.find_by_identity(parts[0])
            if not target:
                await message.answer("Пользователь не найден")
                return
            try:
                days = int(parts[1])
                if days < 1:
                    raise ValueError
            except Exception:
                await message.answer("Некорректное число дней")
                return
            await repo.extend_user_access(target.id, days)
            await ui_repo.set_awaiting(user_id, None)
            await notify_access_change(message.bot, target.id, title="Доступ обновлён", body="Администратор продлил ваш доступ.")
            await message.answer("Доступ продлен.")
            return

        if ui.awaiting_input == "admin_find_user":
            target = await user_repo.find_by_identity(text)
            await ui_repo.set_awaiting(user_id, None)
            if not target:
                await message.answer("Пользователь не найден")
                return
            await _render_user_card(session, message, target.id)
            return

        if ui.awaiting_input == "admin_open_user":
            if not text.isdigit():
                await message.answer("Введите numeric user_id")
                return
            await ui_repo.set_awaiting(user_id, None)
            await _render_user_card(session, message, int(text))
            return

        if ui.awaiting_input == "admin_extend_user_direct":
            target_user_id = int(meta.get("target_user_id", 0))
            try:
                days = int(text)
                if days < 1:
                    raise ValueError
            except Exception:
                await message.answer("Введите положительное количество дней")
                return
            await repo.extend_user_access(target_user_id, days)
            await ui_repo.set_awaiting(user_id, None)
            await notify_access_change(message.bot, target_user_id, title="Доступ обновлён", body="Администратор продлил ваш доступ.")
            await message.answer("Доступ продлен.")
            return

        if ui.awaiting_input == "admin_user_grant_direct":
            if not text.isdigit():
                await message.answer("Введите ID ключа")
                return
            key_id = int(text)
            target_user_id = int(meta.get("target_user_id", 0))
            ok, key = await repo.grant_key_to_user(key_id, target_user_id)
            await ui_repo.set_awaiting(user_id, None)
            if not ok or not key:
                await message.answer("Не удалось выдать ключ")
                return
            await notify_access_change(message.bot, target_user_id, title="Доступ обновлён", body="Администратор выдал вам лицензионный ключ.")
            await message.answer("Ключ выдан пользователю.")
            return

    if ui.awaiting_input == "key":
        ok, key_row = await KeysRepo(session).activate_key(value=text, user_id=user_id)
        if not ok:
            await message.answer("❌ Ключ недействителен, истёк или лимит активаций исчерпан.")
            return
        await ui_repo.set_awaiting(user_id, None)
        if key_row is not None:
            await notify_access_change(message.bot, user_id, title="Доступ обновлён", body="Ваш лицензионный ключ был активирован.")
        await _safe_render_call(render, "show_menu", session, chat_id, user_id)
        return

    if ui.awaiting_input == "topic_title":
        if len(text) < 3:
            await message.answer("Слишком коротко. Напиши тему чуть подробнее 🙂")
            return
        await ui_repo.set_awaiting(user_id, None)
        topic = await TopicRepo(session).create_draft(user_id=user_id, title=text, source_type="topic")
        await _safe_render_call(render, "show_format_pick", session, chat_id, user_id, topic_id=topic.id, title=topic.title)
        return
