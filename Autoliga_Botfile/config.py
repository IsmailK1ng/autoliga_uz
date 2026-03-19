import os
from dotenv import load_dotenv

# Loyiha rootini aniqlaymiz (Autoliga_Botfile papkasi tashqarisi)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Root papkadan .env yuklash
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
MEDIA_ROOT = os.getenv(
    "MEDIA_ROOT",
    os.path.join(PROJECT_ROOT, "media")  # agar .env da bo'lmasa
)
# Django API URL (bot API orqali ishlaydi)
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000")
BOT_API_TOKEN = os.getenv("BOT_API_TOKEN", "")