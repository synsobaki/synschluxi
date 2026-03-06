from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_view():
    text = (
        "<b>UMKOVO</b>\n"
        "Интеллектуальная система освоения тем\n\n"
        "Выберите действие:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать конспект", callback_data="create")],
            [InlineKeyboardButton(text="📚 Архив", callback_data="archive")],
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        ]
    )

    return text, keyboard