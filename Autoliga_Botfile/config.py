import os
from dotenv import load_dotenv

# Load .env from project root (one level up from this file)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media"))