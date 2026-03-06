from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_panel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🗝 Ключи", callback_data="adm:keys:menu")
    b.button(text="👥 Пользователи", callback_data="adm:users:menu")
    b.button(text="📊 Статистика", callback_data="adm:stats:menu")
    b.adjust(1)
    return b.as_markup()


def admin_keys_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Создать ключ", callback_data="adm:key:create")
    b.button(text="📋 Список ключей", callback_data="adm:key:list")
    b.button(text="🔎 Найти ключ", callback_data="adm:key:find")
    b.button(text="⬅ Назад", callback_data="adm:back:panel")
    b.adjust(1)
    return b.as_markup()


def admin_users_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔎 Найти пользователя", callback_data="adm:user:find")
    b.button(text="📋 Список пользователей", callback_data="adm:user:list")
    b.button(text="⬅ Назад", callback_data="adm:back:panel")
    b.adjust(1)
    return b.as_markup()


def admin_days_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="7 дней", callback_data="adm:days:7")
    b.button(text="30 дней", callback_data="adm:days:30")
    b.button(text="90 дней", callback_data="adm:days:90")
    b.button(text="N дней…", callback_data="adm:days:custom")
    b.adjust(2, 2)
    b.row(InlineKeyboardButton(text="⬅ Назад", callback_data="adm:keys:menu"))
    return b.as_markup()


def admin_uses_kb(days: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="1", callback_data=f"adm:uses:{days}:1")
    b.button(text="5", callback_data=f"adm:uses:{days}:5")
    b.button(text="10", callback_data=f"adm:uses:{days}:10")
    b.button(text="25", callback_data=f"adm:uses:{days}:25")
    b.button(text="50", callback_data=f"adm:uses:{days}:50")
    b.button(text="100", callback_data=f"adm:uses:{days}:100")
    b.button(text="N активаций…", callback_data=f"adm:uses_custom:{days}")
    b.adjust(3, 3, 1)
    b.row(InlineKeyboardButton(text="⬅ Назад", callback_data="adm:back:days"))
    return b.as_markup()


def admin_key_row_actions_kb(key_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Открыть", callback_data=f"adm:keycard:{key_id}")
    b.button(text="Выдать", callback_data=f"adm:grant:{key_id}")
    b.adjust(2)
    return b.as_markup()


def admin_key_card_kb(key_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="👤 Выдать пользователю", callback_data=f"adm:grant:{key_id}")
    b.button(text="📅 Изменить срок", callback_data=f"adm:editdays:{key_id}")
    b.button(text="♾ Изменить лимит", callback_data=f"adm:edituses:{key_id}")
    b.button(text="⏩ Продлить доступ", callback_data=f"adm:extend:{key_id}")
    b.button(text="🔁 Отключить/включить", callback_data=f"adm:toggle:{key_id}")
    b.button(text="🗑 Удалить ключ", callback_data=f"adm:delete:{key_id}")
    b.button(text="⬅ К списку", callback_data="adm:key:list")
    b.adjust(1)
    return b.as_markup()


def admin_user_card_kb(user_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Выдать ключ", callback_data=f"adm:usergrant:{user_id}")
    b.button(text="⏩ Продлить доступ", callback_data=f"adm:userextend:{user_id}")
    b.button(text="⛔ Отключить доступ", callback_data=f"adm:useroff:{user_id}")
    b.button(text="🗑 Удалить ключ", callback_data=f"adm:userdelkey:{user_id}")
    b.button(text="📚 Посмотреть темы", callback_data=f"adm:usertopics:{user_id}")
    b.button(text="⬅ Пользователи", callback_data="adm:users:menu")
    b.adjust(1)
    return b.as_markup()
