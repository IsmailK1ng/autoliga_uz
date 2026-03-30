import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env_path = os.path.join(PROJECT_ROOT, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Docker/production: env vars are injected via docker-compose / OS environment.
    logger.debug(".env fayli topilmadi (%s) — environment variables dan o'qiladi.", env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi!")

# MEDIA_ROOT ni Django settings dan olamiz 
# local va serverda ham to'g'ri path bo'ladi
try:
    from django.conf import settings as django_settings

    MEDIA_ROOT = str(django_settings.MEDIA_ROOT)
except Exception:
    # Django setup bo'lmagan holat uchun fallback
    MEDIA_ROOT = os.path.join(PROJECT_ROOT, "media")

# DATABASE_URL, SITE_URL, BOT_API_TOKEN — o'chirildi (bot Django ORM ishlatadi)