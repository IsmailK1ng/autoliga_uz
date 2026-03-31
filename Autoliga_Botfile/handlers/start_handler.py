import os
import sys

from aiogram import types
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from main.services.bot_service import BotService

# Django setup (agar alohida ishga tushirilsa)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")


@sync_to_async
def get_or_create_user(
    telegram_id: int,
    first_name: str,
    last_name: str,
    language: str,
    username: str = None,
):
    user, created = BotService.create_or_update_telegram_user(
        telegram_id,
        first_name=first_name,
        username=username,
        language=language or "uz",
    )
    return user, created


@sync_to_async
def save_phone(telegram_id: int, phone: str):
    user, created = BotService.create_or_update_telegram_user(telegram_id, phone=phone)
    return user


async def start_handler(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    language = message.from_user.language_code or "uz"
    username = message.from_user.username

    user, created = await get_or_create_user(
        telegram_id, first_name, last_name, language, username
    )

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📞 Telefon yuborish",
                                   request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        f"Salom {first_name}! Telefon raqamingizni yuboring.", reply_markup=keyboard
    )


async def contact_handler(message: types.Message, state: FSMContext):
    if not message.contact:
        return

    if message.contact.user_id != message.from_user.id:
        await message.answer("❌ Faqat o'z raqamingizni yuboring!")
        return

    phone = message.contact.phone_number
    telegram_id = message.from_user.id

    await save_phone(telegram_id, phone)
    await message.answer(
        "✅ Telefon raqamingiz saqlandi!",
        reply_markup=types.ReplyKeyboardRemove()
    )