from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Awaitable, Dict, Any


class OneScreenMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.main_message: dict[int, int] = {}  # user_id -> main message_id

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ):
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        data["user_id"] = user_id
        data["main_message"] = self.main_message
        return await handler(event, data)