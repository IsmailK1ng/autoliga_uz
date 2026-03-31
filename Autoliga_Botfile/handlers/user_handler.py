import os
import sys

from aiogram import types
from asgiref.sync import sync_to_async
from main.services.bot_service import BotService

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

@sync_to_async
def get_user(telegram_id: int):
    return BotService.get_telegram_user(telegram_id)


@sync_to_async
def update_user_field(telegram_id: int, **kwargs):
    user, created = BotService.create_or_update_telegram_user(telegram_id, **kwargs)
    return user


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