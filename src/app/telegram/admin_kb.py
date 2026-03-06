from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_panel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔑 Создать мульти-ключ", callback_data="adm:mk:0")
    b.adjust(1)
    return b.as_markup()


def admin_days_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="7 дней", callback_data="adm:days:7")
    b.button(text="30 дней", callback_data="adm:days:30")
    b.button(text="90 дней", callback_data="adm:days:90")
    b.button(text="N дней…", callback_data="adm:days:custom")
    b.adjust(2, 2)
    b.row(InlineKeyboardButton(text="⬅ Назад", callback_data="adm:back:panel"))
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