import os
import sys
from aiogram import types
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

from main.models import TelegramUser


@sync_to_async
def get_user(telegram_id: int):
    try:
        return TelegramUser.objects.get(telegram_id=telegram_id)
    except ObjectDoesNotExist:
        return None


@sync_to_async
def update_user_field(telegram_id: int, **kwargs):
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        for key, value in kwargs.items():
            if value is not None:
                setattr(user, key, value)
        user.save(update_fields=list(kwargs.keys()))
        return user
    except ObjectDoesNotExist:
        return None


async def profile_handler(message: types.Message):
    telegram_id = message.from_user.id
    user = await get_user(telegram_id)

    if not user:
        await message.answer("❌ Profil topilmadi. /start buyrug'ini yuboring.")
        return

    text = (
        f"👤 <b>Profilingiz</b>\n\n"
        f"Ism: {user.first_name or '—'}\n"
        f"Telefon: {user.phone or '—'}\n"
        f"Yosh: {user.age or '—'}\n"
        f"Viloyat: {user.region or '—'}\n"
        f"Til: {'O\'zbekcha' if user.language == 'uz' else 'Русский'}"
    )
    await message.answer(text, parse_mode="HTML")
