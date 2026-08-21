import os
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from cachetools import TTLCache
from bot.database import async_session, Settings
from bot.config import ADMIN_IDS

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 1.0):
        self.cache = TTLCache(maxsize=10000, ttl=rate_limit)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        state = data.get("state")
        if state:
            current_state = await state.get_state()
            if current_state == "Task:processing":
                if isinstance(event, CallbackQuery):
                    await event.answer("Kuting, amaliyot bajarilmoqda...", show_alert=False)
                return

        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            
        if user_id:
            if user_id in self.cache:
                if isinstance(event, CallbackQuery):
                    await event.answer("Kuting...", show_alert=False)
                return
            self.cache[user_id] = True
            
        return await handler(event, data)

class MaintenanceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        chat_type = "private"
        if isinstance(event, Message):
            user_id = event.from_user.id
            chat_type = event.chat.type
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            chat_type = event.message.chat.type if event.message else "private"
        else:
            return await handler(event, data)
            
        if chat_type != "private":
            return
            
        if user_id in ADMIN_IDS:
            return await handler(event, data)
            
        async with async_session() as session:
            from bot.database import User
            user = await session.get(User, user_id)
            if user and user.is_banned:
                if isinstance(event, Message):
                    await event.answer("🚫 Kechirasiz, sizning akkauntingiz bloklangan.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 Akkauntingiz bloklangan.", show_alert=True)
                return
                
            # Restrict unregistered users
            is_start_cmd = isinstance(event, Message) and event.text and event.text.startswith("/start")
            is_tos = isinstance(event, Message) and event.text == "✅ Qoidalarga roziman"
            is_contact = isinstance(event, Message) and event.contact is not None
            is_check_sub = isinstance(event, CallbackQuery) and event.data == "check_sub"
            
            if not user and not (is_start_cmd or is_tos or is_contact or is_check_sub):
                if isinstance(event, Message):
                    await event.answer("Siz ro'yxatdan o'tmagansiz. Qaytadan boshlash uchun /start ni bosing.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("Ro'yxatdan o'tmagansiz.", show_alert=True)
                return
                
            settings = await session.get(Settings, 1)
            if settings and settings.is_maintenance:
                if isinstance(event, Message):
                    await event.answer("🚧 Tizimda texnik ishlar olib borilmoqda. Tizim tez orada o'z ishini davom ettiradi!")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚧 Tizimda texnik ishlar olib borilmoqda.", show_alert=True)
                return
                
        return await handler(event, data)
