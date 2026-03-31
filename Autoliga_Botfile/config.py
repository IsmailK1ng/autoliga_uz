import os
import logging
from dotenv import load_dotenv
logger = logging.getLogger(__name__)

# Loyiha ildiz papkasini aniqlash
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# .env yuklash
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    logger.warning(".env fayli topilmadi, tizim o'zgaruvchilaridan foydalaniladi.")

# Bot sozlamalari
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    # Bu yerda xatolikni aniqroq ko'rsatamiz
    raise EnvironmentError("Muhim xato: BOT_TOKEN topilmadi. .env faylini tekshiring!")

# Sayt URL
SITE_URL = os.getenv("SITE_URL", "https://autoliga.uz")

# Django settings bilan ulanish
try:
    from django.conf import settings
    MEDIA_ROOT = settings.MEDIA_ROOT
except Exception as e:
    logger.info("Django yuklanmadi, fallback media path ishlatiladi.")
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")