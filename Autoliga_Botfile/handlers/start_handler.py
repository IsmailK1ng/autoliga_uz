import os
import sys
import django
from aiogram import types
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist

# Django setup (agar alohida ishga tushirilsa)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

from main.models import TelegramUser


@sync_to_async
def get_or_create_user(telegram_id: int, first_name: str, last_name: str, language: str, username: str = None):
    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'first_name': first_name,
            'username': username,
            'language': language or 'uz',
        }
    )
    return user, created


@sync_to_async
def save_phone(telegram_id: int, phone: str):
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        user.phone = phone
        user.save(update_fields=['phone'])
        return user
    except ObjectDoesNotExist:
        return None


async def start_handler(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    language = message.from_user.language_code or "uz"
    username = message.from_user.username

    user, created = await get_or_create_user(telegram_id, first_name, last_name, language, username)

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📞 Telefon yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(f"Salom {first_name}! Telefon raqamingizni yuboring.", reply_markup=keyboard)


async def contact_handler(message: types.Message, state: FSMContext):
    if not message.contact:
        return

    if message.contact.user_id != message.from_user.id:
        await message.answer("❌ Faqat o'z raqamingizni yuboring!")
        return

    phone = message.contact.phone_number
    telegram_id = message.from_user.id

    await save_phone(telegram_id, phone)
    await message.answer("✅ Telefon raqamingiz saqlandi!", reply_markup=types.ReplyKeyboardRemove())
