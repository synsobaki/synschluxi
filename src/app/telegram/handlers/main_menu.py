from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest

from app.telegram.ui.renderer import main_menu_view

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, main_message: dict, user_id: int):
    text, keyboard = main_menu_view()
    sent = await message.answer(text, reply_markup=keyboard)
    main_message[user_id] = sent.message_id


@router.callback_query()
async def callback_handler(callback: CallbackQuery, main_message: dict, user_id: int):
    # пока любой callback просто перерисовывает меню
    text, keyboard = main_menu_view()
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()