import asyncio
import html as html_module
import logging
import os
import re
import sys
import django
from collections import OrderedDict
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ── 1. Load .env BEFORE Django setup (settings.py reads env vars) ───────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# ── 2. Django setup BEFORE any model imports ────────────────────────────────
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
# Guard against double-setup (when imported from apps.py inside running Django)
from django.apps import apps as _django_apps
if not _django_apps.ready:
    django.setup()

# ── 3. Django imports (safe only after setup) ────────────────────────────────
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import close_old_connections
from django.db import transaction
from django.utils import timezone
from main.models import (Dealer, Product, ProductCategory, TelegramUser,
                         TestDriveRequest)
from main.services.bot_service import BotService

# ── 4. Third-party imports ───────────────────────────────────────────────────
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (FSInputFile, KeyboardButton, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from asgiref.sync import sync_to_async
from config import BOT_TOKEN, MEDIA_ROOT, SITE_URL


# ================= LOGGING =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.log"),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class DjangoDBMiddleware:
    """Refresh stale Django DB connections before each update."""

    async def __call__(self, handler, event, data):
        close_old_connections()
        return await handler(event, data)


dp.update.outer_middleware(DjangoDBMiddleware())

# ================= DATABASE FUNCTIONS =================


@sync_to_async(thread_sensitive=False)
def get_user_by_telegram_id(telegram_id: int) -> TelegramUser | None:
    return BotService.get_telegram_user(telegram_id)


@sync_to_async(thread_sensitive=False)
def update_or_create_user(telegram_id: int, **kwargs) -> TelegramUser:
    user, created = BotService.create_or_update_telegram_user(telegram_id, **kwargs)
    return user


@sync_to_async(thread_sensitive=False)
def get_brands(lang: str = "uz") -> list[dict]:
    return BotService.get_brands(lang)


@sync_to_async(thread_sensitive=False)
def get_cars_by_brand(brand_id: int, lang: str = "uz") -> list[dict]:
    return BotService.get_cars_by_brand(brand_id, lang)


@sync_to_async(thread_sensitive=False)
def get_car_detail(car_id: int, lang: str = "uz") -> dict | None:
    return BotService.get_car_detail(car_id, lang)


@sync_to_async(thread_sensitive=False)
def get_dealers(lang: str = "uz") -> list[dict]:
    return BotService.get_dealers(lang)


@sync_to_async(thread_sensitive=False)
def get_test_drive_data(lang: str = "uz") -> dict:
    return BotService.get_test_drive_form_data(lang)


@sync_to_async(thread_sensitive=False)
def create_test_drive_request(data: dict) -> tuple[TestDriveRequest | None, str | None]:
    return BotService.create_test_drive_request(data)


# ================= HELPERS =================


def sanitize_name(text):
    if not isinstance(text, str):
        return None
    text = text.strip()
    if len(text) < 2 or len(text) > 30:
        return None
    if not re.fullmatch(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ\s\-'`]{2,30}", text):
        return None
    return text


def get_image_path(relative_url: str) -> str | None:
    if not relative_url:
        return None
    path = relative_url
    if path.startswith("/media/"):
        path = path[7:]
    elif path.startswith("media/"):
        path = path[6:]
    safe_path = os.path.normpath(path).lstrip("/\\")
    full_path = os.path.join(MEDIA_ROOT, safe_path)
    if not full_path.startswith(os.path.abspath(MEDIA_ROOT)):
        return None
    return full_path if os.path.exists(full_path) else None


# ================= DEALER REGION LABELS =================

DEALER_REGION_LABELS = {
    "uz": {
        "qoraqalpogiston": "Qoraqalpog'iston Respublikasi",
        "xorazm": "Xorazm viloyati",
        "buxoro": "Buxoro viloyati",
        "navoiy": "Navoiy viloyati",
        "samarqand": "Samarqand viloyati",
        "qashqadaryo": "Qashqadaryo viloyati",
        "surxondaryo": "Surxondaryo viloyati",
        "jizzax": "Jizzax viloyati",
        "sirdaryo": "Sirdaryo viloyati",
        "toshkent-viloyati": "Toshkent viloyati",
        "toshkent-shahri": "Toshkent shahri",
        "namangan": "Namangan viloyati",
        "andijon": "Andijon viloyati",
        "fargona": "Farg'ona viloyati",
    },
    "ru": {
        "qoraqalpogiston": "Республика Каракалпакстан",
        "xorazm": "Хорезмская область",
        "buxoro": "Бухарская область",
        "navoiy": "Навоийская область",
        "samarqand": "Самаркандская область",
        "qashqadaryo": "Кашкадарьинская область",
        "surxondaryo": "Сурхандарьинская область",
        "jizzax": "Джизакская область",
        "sirdaryo": "Сырдарьинская область",
        "toshkent-viloyati": "Ташкентская область",
        "toshkent-shahri": "город Ташкент",
        "namangan": "Наманганская область",
        "andijon": "Андижанская область",
        "fargona": "Fergana region",
    },
    "en": {
        "qoraqalpogiston": "Republic of Karakalpakstan",
        "xorazm": "Khorezm region",
        "buxoro": "Bukhara region",
        "navoiy": "Navoi region",
        "samarqand": "Samarkand region",
        "qashqadaryo": "Kashkadarya region",
        "surxondaryo": "Surkhandarya region",
        "jizzax": "Jizzakh region",
        "sirdaryo": "Syrdarya region",
        "toshkent-viloyati": "Tashkent region",
        "toshkent-shahri": "Tashkent city",
        "namangan": "Namangan region",
        "andijon": "Andijan region",
        "fargona": "Fergana region",
    },
}

# ================= REGIONS =================

UZ_REGIONS = {
    "uz": {
        "Toshkent shahri": [
            "Yunusobod",
            "Chilonzor",
            "Olmazor",
            "Yashnobod",
            "Mirzo Ulug'bek",
            "Sergeli",
            "Bektemir",
        ],
        "Toshkent viloyati": [
            "Zangiota",
            "Chinoz",
            "Parkent",
            "Bo'ka",
            "Ohangaron",
            "Oqqo'rg'on",
            "Bekobod",
        ],
        "Samarqand": [
            "Urgut",
            "Kattaqo'rg'on",
            "Bulung'ur",
            "Narpay",
            "Toyloq",
            "Qo'shrabot",
            "Ishtixon",
        ],
        "Andijon": [
            "Asaka",
            "Shahrixon",
            "Xo'jaobod",
            "Qo'rg'ontepa",
            "Baliqchi",
            "Ulug'nor",
            "Oltinko'l",
            "Andijon",
        ],
        "Farg'ona": [
            "Qo'qon",
            "Marg'ilon",
            "Farg'ona",
            "Oltiariq",
            "Beshariq",
            "Quva",
            "Rishton",
        ],
        "Namangan": [
            "Chust",
            "Kosonsoy",
            "Namangan",
            "Pop",
            "To'raqo'rg'on",
            "Uychi",
            "Mingbuloq",
        ],
        "Buxoro": [
            "G'ijduvon",
            "Kogon",
            "Buxoro",
            "Vobkent",
            "Peshku",
            "Romitan",
            "Shofirkon",
        ],
        "Xorazm": [
            "Urganch",
            "Xiva",
            "Shovot",
            "Gurlan",
            "Yangiariq",
            "Bog'ot",
            "Xonqa",
        ],
        "Qashqadaryo": [
            "Qarshi",
            "Shahrisabz",
            "G'uzor",
            "Chiroqchi",
            "Koson",
            "Kitob",
            "Dehqonobod",
        ],
        "Surxondaryo": [
            "Termiz",
            "Denov",
            "Boysun",
            "Muzrabot",
            "Sariosiyo",
            "Qumqo'rg'on",
            "Sherobod",
        ],
        "Jizzax": [
            "Zomin",
            "G'allaorol",
            "Zarbdor",
            "Do'stlik",
            "Yangiobod",
            "Arnasoy",
            "Baxmal",
        ],
        "Sirdaryo": [
            "Guliston",
            "Yangiyer",
            "Sirdaryo",
            "Oqoltin",
            "Shirin",
            "Boyovut",
        ],
        "Navoiy": [
            "Zarafshon",
            "Karmana",
            "Navoiy",
            "Qiziltepa",
            "Tomdi",
            "Xatirchi",
            "Konimex",
        ],
        "Qoraqalpog'iston": [
            "Nukus",
            "Xo'jayli",
            "Kegeyli",
            "Chimboy",
            "Taxtako'pir",
            "Beruniy",
            "Qo'ng'irot",
        ],
    },
    "ru": {
        "Ташкент (город)": [
            "Юнусабад",
            "Чиланзар",
            "Олмазар",
            "Яшнабад",
            "Мирзо-Улугбек",
            "Сергели",
            "Бектемир",
        ],
        "Ташкентская область": [
            "Зангиата",
            "Чиноз",
            "Паркент",
            "Бука",
            "Ахангаран",
            "Аккурган",
            "Бекабад",
        ],
        "Самарканд": [
            "Ургут",
            "Каттакурган",
            "Булунгур",
            "Нарпай",
            "Тайлак",
            "Кошрабад",
            "Иштихон",
        ],
        "Андижан": [
            "Асака",
            "Шахрихан",
            "Ходжаабад",
            "Курганtepa",
            "Балыкчи",
            "Улугнор",
            "Алтынкуль",
            "Андижан",
        ],
        "Фергана": [
            "Коканд",
            "Маргилан",
            "Фергана",
            "Олтиарик",
            "Бешарик",
            "Кува",
            "Риштан",
        ],
        "Наманган": [
            "Чуст",
            "Косонсой",
            "Наманган",
            "Поп",
            "Туракурган",
            "Уйчи",
            "Мингбулак",
        ],
        "Бухара": [
            "Гиждуван",
            "Коган",
            "Бухара",
            "Вабкент",
            "Пешку",
            "Ромитан",
            "Шафиркан",
        ],
        "Хорезм": ["Ургенч", "Хива", "Шават", "Гурлан", "Янгиарик", "Богот", "Ханка"],
        "Кашкадарья": [
            "Карши",
            "Шахрисабз",
            "Гузар",
            "Чирокчи",
            "Касан",
            "Китаб",
            "Дехканабад",
        ],
        "Сурхандарья": [
            "Термез",
            "Денов",
            "Байсун",
            "Музрабад",
            "Сариосиё",
            "Кумкурган",
            "Шерабад",
        ],
        "Джизак": [
            "Зомин",
            "Галляарал",
            "Зарбдар",
            "Дустлик",
            "Янгиобод",
            "Арнасай",
            "Бахмал",
        ],
        "Сырдарья": ["Гулистан", "Янгиер", "Сырдарья", "Акалтын", "Ширин", "Баяут"],
        "Навои": [
            "Зарафшан",
            "Кармана",
            "Навои",
            "Кызылтепа",
            "Томди",
            "Хатирчи",
            "Конимех",
        ],
        "Каракалпакстан": [
            "Нукус",
            "Ходжейли",
            "Кегейли",
            "Чимбай",
            "Тахиаташ",
            "Беруний",
            "Кунград",
        ],
    },
}

# ================= FSM STATES =================


class RegStates(StatesGroup):
    first_name = State()
    confirm_name = State()
    age = State()
    confirm_age = State()
    region = State()
    confirm_region = State()
    district = State()
    confirm_district = State()
    phone = State()


class NavStates(StatesGroup):
    choose_brand = State()
    choose_car = State()


class TestDriveStates(StatesGroup):
    choose_dealer = State()
    choose_product = State()
    choose_date = State()
    choose_time = State()
    confirm = State()


# ================= KEYBOARDS =================

LANG_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")],
        [KeyboardButton(text="🇺🇸 English")]
    ],
    resize_keyboard=True,
)


MESSAGES = {
    "uz": {
        "choose_lang": "Tilni tanlang 🌐",
        "send_phone": "Telefoningizni yuboring 📞",
        "send_first_name": "Ismingizni kiriting",
        "send_age": "Yoshingizni kiriting (masalan: 25)",
        "wrong_age": "Yosh noto'g'ri ❌\nFaqat raqam kiriting (5-100)",
        "choose_region": "Viloyatingizni tanlang",
        "choose_district": "Tumaningizni tanlang",
        "saved": "Ma'lumotlaringiz saqlandi ✅",
        "wrong_format": "Format noto'g'ri ❌",
        "choose_from_list": "Iltimos ro'yxatdan tanlang",
        "main_menu": "Asosiy menyu 👇",
        "welcome_back": "Xush kelibsiz 👋\nAsosiy menyu:",
        "no_cars": "Hozircha avtomobillar mavjud emas.",
        "choose_brand": "🚗 Marka tanlang:",
        "choose_model": "Model tanlang:",
        "back_btn": "🔙 Orqaga",
        "dealers_title": "🏢 Dilerlik markazlari:\n\nYaqin orada ko'proq ma'lumot qo'shiladi.\n\nSaytimizga tashrif buyuring: autoliga.uz/dealers/",
        "change_lang_btn": "🌐 Tilni o'zgartirish",
        "lang_changed": "Til o'zgartirildi ✅\nAsosiy menyu:",
        "unsupported": "Iltimos faqat matn yuboring ✍️",
        "invalid_name": (
            "❌ Ism noto'g'ri kiritildi!\n\n"
            "✅ Qoidalar:\n"
            "• Faqat harflar (lotin yoki kirill)\n"
            "• Kamida 2 ta harf\n"
            "• Ko'pi bilan 30 ta harf\n"
            "• Raqam, emoji, belgilar yo'q"
        ),
        "confirm_name": "Ismingiz: <b>{}</b>\n\nTo'g'ri kiritdingizmi?",
        "confirm_age": "Yoshingiz: <b>{}</b>\n\nTo'g'ri kiritdingizmi?",
        "confirm_region": "Viloyatingiz: <b>{}</b>\n\nTo'g'ri tanladingizmi?",
        "confirm_district": "Tumaningiz: <b>{}</b>\n\nTo'g'ri tanladingizmi?",
        "yes_btn": "✅ Ha",
        "no_btn": "❌ Yo'q, qayta kiritaman",
        "test_drive_btn": "🚗 Test-drayvga yozilish",
        "td_choose_dealer": "🏢 Diler markazni tanlang:",
        "td_choose_product": "🚗 Avtomobil modelini tanlang:",
        "td_choose_date": "📅 Sanani tanlang:",
        "td_choose_time": "🕐 Vaqtni tanlang:",
        "td_enter_name": "👤 Ismingizni kiriting:",
        "td_enter_phone": "📞 Telefon raqamingizni kiriting:\nMasalan: +998901234567",
        "td_confirm": (
            "📋 <b>Test-drayv ma'lumotlari:</b>\n\n"
            "🏢 Diler: <b>{dealer}</b>\n"
            "🚗 Model: <b>{product}</b>\n"
            "📅 Sana: <b>{date}</b>\n"
            "🕐 Vaqt: <b>{time}</b>\n"
            "👤 Ism: <b>{name}</b>\n"
            "📞 Telefon: <b>{phone}</b>\n\n"
            "Hammasi to'g'rimi?"
        ),
        "td_success": "✅ Test-drayvga muvaffaqiyatli yozildingiz!\nTez orada siz bilan bog'lanamiz.",
        "td_no_dealers": (
            "⚠️ Hozircha test-drayv uchun dilerlik markazlari qo'shilmagan.\n"
            "Iltimos, birozdan so'ng qayta urinib ko'ring."
        ),
        "td_error": "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
        "td_invalid_date": "❌ Iltimos ro'yxatdan sana tanlang.",
        "td_invalid_phone": "❌ Telefon noto'g'ri. +998XXXXXXXXX formatida kiriting.",
        "td_daily_limit": "⚠️ Kuniga 2 tadan ortiq test-drayv ariza yuborib bo'lmaydi.\nErtaga qayta urinib ko'ring.",
    },
    "ru": {
        "choose_lang": "Выберите язык 🌐",
        "send_phone": "Отправьте ваш номер телефона 📞",
        "send_first_name": "Введите имя",
        "send_age": "Введите ваш возраст (например: 25)",
        "wrong_age": "Неверный возраст ❌\nВведите только цифры (5-100)",
        "choose_region": "Выберите область",
        "choose_district": "Выберите район",
        "saved": "Ваши данные сохранены ✅",
        "wrong_format": "Неверный формат ❌",
        "choose_from_list": "Пожалуйста выберите из списка",
        "main_menu": "Главное меню 👇",
        "welcome_back": "Добро пожаловать 👋\nГлавное меню:",
        "no_cars": "Автомобили пока не добавлены.",
        "choose_brand": "🚗 Выберите марку:",
        "choose_model": "Выберите модель:",
        "back_btn": "🔙 Назад",
        "dealers_title": "🏢 Дилерские центры:\n\nПодробная информация скоро будет добавлена.\n\nПосетите наш сайт: autoliga.uz/dealers/",
        "change_lang_btn": "🌐 Сменить язык",
        "lang_changed": "Язык изменён ✅\nГлавное меню:",
        "unsupported": "Пожалуйста, отправляйте только текст ✍️",
        "invalid_name": (
            "❌ Имя введено неверно!\n\n"
            "✅ Правила:\n"
            "• Только буквы (латиница или кириллица)\n"
            "• Минимум 2 буквы\n"
            "• Максимум 30 букв\n"
            "• Цифры, эмодзи, символы запрещены"
        ),
        "confirm_name": "Ваше имя: <b>{}</b>\n\nВсё верно?",
        "confirm_age": "Ваш возраст: <b>{}</b>\n\nВсё верно?",
        "confirm_region": "Ваша область: <b>{}</b>\n\nВсё верно?",
        "confirm_district": "Ваш район: <b>{}</b>\n\nВсё верно?",
        "yes_btn": "✅ Да",
        "no_btn": "❌ Нет, ввести заново",
        "test_drive_btn": "🚗 Записаться на тест-драйв",
        "td_choose_dealer": "🏢 Выберите дилерский центр:",
        "td_choose_product": "🚗 Выберите модель автомобиля:",
        "td_choose_date": "📅 Выберите дату:",
        "td_choose_time": "🕐 Выберите время:",
        "td_enter_name": "👤 Введите ваше имя:",
        "td_enter_phone": "📞 Введите номер телефона:\nНапример: +998901234567",
        "td_confirm": (
            "📋 <b>Данные тест-драйва:</b>\n\n"
            "🏢 Дилер: <b>{dealer}</b>\n"
            "🚗 Модель: <b>{product}</b>\n"
            "📅 Дата: <b>{date}</b>\n"
            "🕐 Время: <b>{time}</b>\n"
            "👤 Имя: <b>{name}</b>\n"
            "📞 Телефон: <b>{phone}</b>\n\n"
            "Всё верно?"
        ),
        "td_success": "✅ Вы успешно записаны на тест-драйв!\nМы скоро свяжемся с вами.",
        "td_no_dealers": (
            "⚠️ Дилерские центры для тест-драйва пока не добавлены.\n"
            "Пожалуйста, попробуйте позже."
        ),
        "td_error": "❌ Произошла ошибка. Попробуйте ещё раз.",
        "td_invalid_date": "❌ Пожалуйста, выберите дату из списка.",
        "td_invalid_phone": "❌ Неверный номер. Введите в формате +998XXXXXXXXX.",
        "td_daily_limit": "⚠️ Дневной лимит: не более 2 заявок в день.\nПопробуйте завтра.",
    },
    "en": {
        "choose_lang": "Choose language 🌐",
        "send_phone": "Send your phone number 📞",
        "send_first_name": "Enter your name",
        "send_age": "Enter your age (example: 25)",
        "wrong_age": "Invalid age ❌\nEnter only numbers (5-100)",
        "choose_region": "Choose your region",
        "choose_district": "Choose your district",
        "saved": "Your data is saved ✅",
        "wrong_format": "Invalid format ❌",
        "choose_from_list": "Please choose from the list",
        "main_menu": "Main menu 👇",
        "welcome_back": "Welcome back 👋\nMain menu:",
        "no_cars": "Cars are not available yet.",
        "choose_brand": "🚗 Choose brand:",
        "choose_model": "Choose model:",
        "back_btn": "🔙 Back",
        "dealers_title": "🏢 Dealerships:\n\nMore information will be added soon.\n\nVisit our website: autoliga.uz/dealers/",
        "change_lang_btn": "🌐 Change language",
        "lang_changed": "Language changed ✅\nMain menu:",
        "unsupported": "Please send only text ✍️",
        "invalid_name": (
            "❌ Name entered incorrectly!\n\n"
            "✅ Rules:\n"
            "• Only letters (Latin or Cyrillic)\n"
            "• Minimum 2 letters\n"
            "• Maximum 30 letters\n"
            "• Numbers, emojis, symbols prohibited"
        ),
        "confirm_name": "Your name: <b>{}</b>\n\nIs it correct?",
        "confirm_age": "Your age: <b>{}</b>\n\nIs it correct?",
        "confirm_region": "Your region: <b>{}</b>\n\nIs it correct?",
        "confirm_district": "Your district: <b>{}</b>\n\nIs it correct?",
        "yes_btn": "✅ Yes",
        "no_btn": "❌ No, enter again",
        "test_drive_btn": "🚗 Book test drive",
        "td_choose_dealer": "🏢 Choose dealership:",
        "td_choose_product": "🚗 Choose car model:",
        "td_choose_date": "📅 Choose date:",
        "td_choose_time": "🕐 Choose time:",
        "td_enter_name": "👤 Enter your name:",
        "td_enter_phone": "📞 Enter your phone number:\nExample: +998901234567",
        "td_confirm": (
            "📋 <b>Test drive details:</b>\n\n"
            "🏢 Dealer: <b>{dealer}</b>\n"
            "🚗 Model: <b>{product}</b>\n"
            "📅 Date: <b>{date}</b>\n"
            "🕐 Time: <b>{time}</b>\n"
            "👤 Name: <b>{name}</b>\n"
            "📞 Phone: <b>{phone}</b>\n\n"
            "Is everything correct?"
        ),
        "td_success": "✅ You have successfully booked a test drive!\nWe will contact you soon.",
        "td_no_dealers": (
            "⚠️ Dealerships for test drive are not added yet.\n"
            "Please try again later."
        ),
        "td_error": "❌ An error occurred. Try again.",
        "td_invalid_date": "❌ Please choose a date from the list.",
        "td_invalid_phone": "❌ Invalid number. Enter in format +998XXXXXXXXX.",
        "td_daily_limit": "⚠️ Daily limit: no more than 2 requests per day.\nTry tomorrow.",
    },
}

CHANGE_LANG_BTNS = {
    MESSAGES["uz"]["change_lang_btn"],
    MESSAGES["ru"]["change_lang_btn"],
    MESSAGES["en"]["change_lang_btn"],
}
TEST_DRIVE_BTNS = {MESSAGES["uz"]["test_drive_btn"], MESSAGES["ru"]["test_drive_btn"], MESSAGES["en"]["test_drive_btn"]}

class _LRUDict(OrderedDict):
    """Bounded dict — evicts oldest entry when maxsize exceeded."""
    def __init__(self, maxsize: int = 5000):
        self._maxsize = maxsize
        super().__init__()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)
        if len(self) > self._maxsize:
            self.popitem(last=False)


user_lang: _LRUDict = _LRUDict(maxsize=5000)


def get_confirm_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MESSAGES[lang]["yes_btn"]),
                KeyboardButton(text=MESSAGES[lang]["no_btn"]),
            ],
            [KeyboardButton(text=MESSAGES[lang]["back_btn"])],
        ],
        resize_keyboard=True,
    )


def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    if lang == "ru":
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🚗 Автомобили"),
                    KeyboardButton(text="🏢 Дилерские центры"),
                ],
                [KeyboardButton(text=MESSAGES["ru"]["test_drive_btn"])],
                [KeyboardButton(text=MESSAGES["ru"]["change_lang_btn"])],
            ],
            resize_keyboard=True,
        )
    if lang == "en":
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🚗 Cars"),
                    KeyboardButton(text="🏢 Dealerships"),
                ],
                [KeyboardButton(text=MESSAGES["en"]["test_drive_btn"])],
                [KeyboardButton(text=MESSAGES["en"]["change_lang_btn"])],
            ],
            resize_keyboard=True,
        )
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🚗 Mashinalar"),
                KeyboardButton(text="🏢 Dilerlik markazlari"),
            ],
            [KeyboardButton(text=MESSAGES["uz"]["test_drive_btn"])],
            [KeyboardButton(text=MESSAGES["uz"]["change_lang_btn"])],
        ],
        resize_keyboard=True,
    )
    
    
def build_car_caption(car: dict, lang: str = "uz") -> str:
    """Build car caption based on language"""
    title = car.get('title', '')

    labels = {
        "uz": {
            "year":  "🗓 Yil",
            "price": "💰 Narx",
            "power": "⚡️ Quvvat",
            "fuel":  "⛽️ Yoqilg'i",
        },
        "ru": {
            "year":  "🗓 Год",
            "price": "💰 Цена",
            "power": "⚡️ Мощность",
            "fuel":  "⛽️ Топливо",
        },
        "en": {
            "year":  "🗓 Year",
            "price": "💰 Price",
            "power": "⚡️ Power",
            "fuel":  "⛽️ Fuel",
        },
    }

    L = labels.get(lang, labels["uz"])

    lines = [f"🚗 {title}", ""]

    if car.get("year"):
        lines.append(f"{L['year']}:  {car['year']}")
    if car.get("price"):
        lines.append(f"{L['price']}:  {car['price']}")
    if car.get("power"):
        lines.append(f"{L['power']}:  {car['power']}")
    if car.get("fuel"):
        lines.append(f"{L['fuel']}:  {car['fuel']}")

    return "\n".join(lines)


def get_date_keyboard(back_btn: str, days: int = 14) -> ReplyKeyboardMarkup:
    """Bugundan boshlab N kunlik sana tugmalari (3 ustunli)"""
    today = timezone.localtime(timezone.now()).date()
    rows = []
    row = []
    for i in range(days):
        d = today + timedelta(days=i)
        row.append(KeyboardButton(text=d.strftime("%d.%m.%Y")))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=back_btn)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# ================= MEDIA BLOCKER =================


@dp.message(~F.text & ~F.contact)
async def block_unsupported_media(message: types.Message):
    lang = user_lang.get(message.from_user.id, "uz")
    await message.answer(MESSAGES[lang]["unsupported"])


# ================= START =================


@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    uid = message.from_user.id

    user_data = await get_user_by_telegram_id(uid)  # ← await qo'shildi

    if user_data and user_data.phone and user_data.first_name:
        lang = user_data.language or "uz"
        user_lang[uid] = lang
        await state.clear()
        await message.answer(
            MESSAGES[lang]["welcome_back"], reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        await state.clear()
        await message.answer(MESSAGES["uz"]["choose_lang"], reply_markup=LANG_KEYBOARD)


# ================= TIL O'ZGARTIRISH =================


@dp.message(F.text.in_(CHANGE_LANG_BTNS))
async def request_lang_change(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        MESSAGES["uz"]["choose_lang"] + " / " + MESSAGES["ru"]["choose_lang"] + " / " + MESSAGES["en"]["choose_lang"],
        reply_markup=LANG_KEYBOARD,
    )


# ================= LANGUAGE =================


@dp.message(F.text.startswith("🇺🇿") | F.text.startswith("🇷🇺") | F.text.startswith("🇺🇸"))
async def choose_language(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    if message.text.startswith("🇺🇿"):
        lang = "uz"
    elif message.text.startswith("🇷🇺"):
        lang = "ru"
    else:
        lang = "en"
    user_lang[uid] = lang

    await update_or_create_user(  # ← await qo'shildi
        uid, language=lang, username=message.from_user.username
    )

    user = await get_user_by_telegram_id(uid)  # ← await qo'shildi
    has_profile = bool(user and user.phone and user.first_name)

    if has_profile:
        await state.clear()
        await message.answer(
            MESSAGES[lang]["lang_changed"], reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        await state.set_state(RegStates.first_name)
        await message.answer(
            MESSAGES[lang]["send_first_name"], reply_markup=ReplyKeyboardRemove()
        )


# ================= CONTACT =================


@dp.message(F.contact)
async def save_phone(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    lang = user_lang.get(uid, "uz")

    if message.contact.user_id != uid:
        await message.answer("❌")
        return

    await update_or_create_user(
        uid, phone=message.contact.phone_number
    )  # ← await qo'shildi

    await state.clear()
    await message.answer(
        MESSAGES[lang]["saved"] + "\n\n" + MESSAGES[lang]["main_menu"],
        reply_markup=get_main_menu_keyboard(lang),
    )


# ================= MAIN MENU: MASHINALAR =================


@dp.message(F.text.in_({"🚗 Mashinalar", "🚗 Автомобили", "🚗 Cars"}))
async def show_brands(message: types.Message, state: FSMContext):
    lang = user_lang.get(message.from_user.id, "uz")
    brands = await get_brands(lang)  # ← await qo'shildi

    if not brands:
        await message.answer(MESSAGES[lang]["no_cars"])
        return

    await state.set_state(NavStates.choose_brand)
    await state.update_data(brands={b["name"]: b["id"] for b in brands})

    rows = [[KeyboardButton(text=b["name"])] for b in brands]
    rows.append([KeyboardButton(text=MESSAGES[lang]["back_btn"])])
    kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
    await message.answer(MESSAGES[lang]["choose_brand"], reply_markup=kb)


# ================= MAIN MENU: DILERLAR =================


@dp.message(F.text.in_({"🏢 Dilerlik markazlari", "🏢 Дилерские центры", "🏢 Dealerships"}))
async def show_dealers(message: types.Message):
    lang = user_lang.get(message.from_user.id, "uz")
    dealers = await get_dealers(lang)  # ← await qo'shildi

    if not dealers:
        await message.answer(MESSAGES[lang]["dealers_title"])
        return

    if lang == "uz":
        header = "🏢 <b>Dilerlik markazlari:</b>\n\n"
    elif lang == "ru":
        header = "🏢 <b>Дилерские центры:</b>\n\n"
    else:
        header = "🏢 <b>Dealerships:</b>\n\n"
    lines = []
    for d in dealers:
        block = f"<b>{html_module.escape(d['name'])}</b>"
        if d.get("region"):
            region_label = DEALER_REGION_LABELS.get(lang, {}).get(
                d["region"], d["region"]
            )
            block += f"\n📍 {html_module.escape(region_label)}"
        if d.get("address"):
            block += f"\n🏠 {html_module.escape(d['address'])}"
        if d.get("phone"):
            block += f"\n📞 {html_module.escape(d['phone'])}"
        if d.get("hours"):
            block += f"\n🕐 {html_module.escape(d['hours'])}"
        lines.append(block)

    text = header + "\n\n".join(lines)
    await message.answer(text, parse_mode="HTML")


# ================= MAIN MENU: TEST-DRAYV =================


@dp.message(F.text.in_(TEST_DRIVE_BTNS))
async def start_test_drive(message: types.Message, state: FSMContext):
    lang = user_lang.get(message.from_user.id, "uz")

    td_data = await get_test_drive_data(lang)  # ← await qo'shildi
    dealers = td_data.get("dealers", [])
    if not dealers:
        await message.answer(MESSAGES[lang].get("td_no_dealers", MESSAGES[lang]["td_error"]))
        return

    await state.set_state(TestDriveStates.choose_dealer)
    await state.update_data(
        td_dealers={d["name"]: d["id"] for d in dealers},
        td_products={p["title"]: p["id"] for p in td_data.get("products", [])},
        td_time_slots=td_data.get("time_slots", []),
    )

    rows = [[KeyboardButton(text=d["name"])] for d in dealers]
    rows.append([KeyboardButton(text=MESSAGES[lang]["back_btn"])])
    kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
    await message.answer(MESSAGES[lang]["td_choose_dealer"], reply_markup=kb)


# ================= CATCH-ALL =================


@dp.message()
async def handle_all(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    current_state = await state.get_state()
    lang = user_lang.get(uid, "uz")
    back_btn = MESSAGES[lang]["back_btn"]
    yes_btn = MESSAGES[lang]["yes_btn"]
    no_btn = MESSAGES[lang]["no_btn"]

    if not message.text:
        await message.answer(MESSAGES[lang]["unsupported"])
        return

    text = message.text.strip()

    # ===== BACK BUTTON =====
    if text == back_btn:
        if current_state == RegStates.first_name:
            await state.clear()
            await message.answer(
                MESSAGES[lang]["choose_lang"], reply_markup=LANG_KEYBOARD
            )
        elif current_state in (RegStates.confirm_name, RegStates.age):
            await state.set_state(RegStates.first_name)
            await message.answer(
                MESSAGES[lang]["send_first_name"], reply_markup=ReplyKeyboardRemove()
            )
        elif current_state in (RegStates.confirm_age, RegStates.region):
            await state.set_state(RegStates.age)
            await message.answer(
                MESSAGES[lang]["send_age"], reply_markup=ReplyKeyboardRemove()
            )
        elif current_state in (RegStates.confirm_region, RegStates.district):
            await state.set_state(RegStates.region)
            regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=r)] for r in regions.keys()]
                + [[KeyboardButton(text=back_btn)]],
                resize_keyboard=True,
            )
            await message.answer(MESSAGES[lang]["choose_region"], reply_markup=kb)
        elif current_state in (RegStates.confirm_district, RegStates.phone):
            data = await state.get_data()
            region_name = data.get("reg_region", "")
            regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])
            districts = regions.get(region_name, [])
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=d)] for d in districts]
                + [[KeyboardButton(text=back_btn)]],
                resize_keyboard=True,
            )
            await state.set_state(RegStates.district)
            await message.answer(MESSAGES[lang]["choose_district"], reply_markup=kb)
        elif current_state == NavStates.choose_brand:
            await state.clear()
            await message.answer(
                MESSAGES[lang]["main_menu"], reply_markup=get_main_menu_keyboard(lang)
            )
        elif current_state == NavStates.choose_car:
            brands = await get_brands(lang)  # ← await qo'shildi
            if brands:
                await state.set_state(NavStates.choose_brand)
                await state.update_data(brands={b["name"]: b["id"] for b in brands})
                rows = [[KeyboardButton(text=b["name"])] for b in brands]
                rows.append([KeyboardButton(text=back_btn)])
                kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
                await message.answer(MESSAGES[lang]["choose_brand"], reply_markup=kb)
            else:
                await state.clear()
                await message.answer(
                    MESSAGES[lang]["main_menu"],
                    reply_markup=get_main_menu_keyboard(lang),
                )
        elif current_state and current_state.startswith("TestDriveStates:"):
            await state.clear()
            await message.answer(
                MESSAGES[lang]["main_menu"], reply_markup=get_main_menu_keyboard(lang)
            )
        else:
            await state.clear()
            await message.answer(
                MESSAGES[lang]["main_menu"], reply_markup=get_main_menu_keyboard(lang)
            )
        return

    # ===== BRAND SELECTION =====
    if current_state == NavStates.choose_brand:
        data = await state.get_data()
        brands_map = data.get("brands", {})
        if text not in brands_map:
            await message.answer(MESSAGES[lang]["choose_from_list"])
            return

        brand_id = brands_map[text]
        cars = await get_cars_by_brand(brand_id, lang)  # ← await qo'shildi

        if not cars:
            await message.answer(MESSAGES[lang]["no_cars"])
            return

        await state.set_state(NavStates.choose_car)
        await state.update_data(
            brands=brands_map, cars={c["title"]: c["id"] for c in cars}
        )

        rows = [[KeyboardButton(text=c["title"])] for c in cars]
        rows.append([KeyboardButton(text=back_btn)])
        kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
        await message.answer(
            f"{html_module.escape(text)} — {MESSAGES[lang]['choose_model']}",
            reply_markup=kb,
        )
        return

    # ===== CAR SELECTION =====
    if current_state == NavStates.choose_car:
        data = await state.get_data()
        cars_map = data.get("cars", {})
        if text not in cars_map:
            await message.answer(MESSAGES[lang]["choose_from_list"])
            return

        car_id = cars_map[text]
        car = await get_car_detail(car_id, lang)  # ← await qo'shildi

        if not car:
            await message.answer("❌")
            return

        caption = build_car_caption(car, lang)

        # Create inline button for site
        button_text = "Batafsil ma’lumot" if lang == "uz" else "Подробнее"
        site_url = f"{SITE_URL}/products/{car['slug']}/"
        inline_button = InlineKeyboardButton(text=button_text, url=site_url)
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[[inline_button]])

        image_url = car.get("card_image") or car.get("main_image")
        image_path = get_image_path(image_url) if image_url else None

        if image_path:
            await message.answer_photo(
                photo=FSInputFile(image_path), caption=caption, reply_markup=inline_kb
            )
        else:
            await message.answer(caption, reply_markup=inline_kb)
        return

    # ===== REGISTRATION: FIRST NAME =====
    if current_state == RegStates.first_name:
        name = sanitize_name(text)
        if not name:
            await message.answer(MESSAGES[lang]["invalid_name"])
            return
        await state.update_data(reg_name=name)
        await state.set_state(RegStates.confirm_name)
        await message.answer(
            MESSAGES[lang]["confirm_name"].format(html_module.escape(name)),
            parse_mode="HTML",
            reply_markup=get_confirm_keyboard(lang),
        )
        return

    # ===== CONFIRM NAME =====
    if current_state == RegStates.confirm_name:
        if text == yes_btn:
            data = await state.get_data()
            name = data.get("reg_name", "")
            await update_or_create_user(uid, first_name=name)  # ← await qo'shildi
            await state.set_state(RegStates.age)
            await message.answer(
                MESSAGES[lang]["send_age"], reply_markup=ReplyKeyboardRemove()
            )
        elif text == no_btn:
            await state.set_state(RegStates.first_name)
            await message.answer(
                MESSAGES[lang]["send_first_name"], reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer(MESSAGES[lang]["choose_from_list"])
        return

    # ===== AGE =====
    if current_state == RegStates.age:
        if text.isdigit() and 5 <= int(text) <= 100:
            await state.update_data(reg_age=int(text))
            await state.set_state(RegStates.confirm_age)
            await message.answer(
                MESSAGES[lang]["confirm_age"].format(text),
                parse_mode="HTML",
                reply_markup=get_confirm_keyboard(lang),
            )
        else:
            await message.answer(MESSAGES[lang]["wrong_age"])
        return

    # ===== CONFIRM AGE =====
    if current_state == RegStates.confirm_age:
        if text == yes_btn:
            data = await state.get_data()
            await update_or_create_user(
                uid, age=data.get("reg_age")
            )  # ← await qo'shildi
            await state.set_state(RegStates.region)
            regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=r)] for r in regions.keys()]
                + [[KeyboardButton(text=back_btn)]],
                resize_keyboard=True,
            )
            await message.answer(MESSAGES[lang]["choose_region"], reply_markup=kb)
        elif text == no_btn:
            await state.set_state(RegStates.age)
            await message.answer(
                MESSAGES[lang]["send_age"], reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer(MESSAGES[lang]["choose_from_list"])
        return

    # ===== REGION =====
    if current_state == RegStates.region:
        regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])
        if text in regions:
            await state.update_data(reg_region=text)
            await state.set_state(RegStates.confirm_region)
            await message.answer(
                MESSAGES[lang]["confirm_region"].format(html_module.escape(text)),
                parse_mode="HTML",
                reply_markup=get_confirm_keyboard(lang),
            )
        else:
            await message.answer(MESSAGES[lang]["choose_from_list"])
        return

    # ===== CONFIRM REGION =====
    if current_state == RegStates.confirm_region:
        if text == yes_btn:
            data = await state.get_data()
            region_name = data.get("reg_region", "")
            regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])
            districts = regions.get(region_name, [])
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=d)] for d in districts]
                + [[KeyboardButton(text=back_btn)]],
                resize_keyboard=True,
            )
            await state.set_state(RegStates.district)
            await message.answer(MESSAGES[lang]["choose_district"], reply_markup=kb)
        elif text == no_btn:
            await state.set_state(RegStates.region)
            regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=r)] for r in regions.keys()]
                + [[KeyboardButton(text=back_btn)]],
                resize_keyboard=True,
            )
            await message.answer(MESSAGES[lang]["choose_region"], reply_markup=kb)
        else:
            await message.answer(MESSAGES[lang]["choose_from_list"])
        return

    # ===== DISTRICT =====
    if current_state == RegStates.district:
        data = await state.get_data()
        region_name = data.get("reg_region", "")
        regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])
        valid_districts = regions.get(region_name, [])
        if text not in valid_districts:
            await message.answer(MESSAGES[lang]["choose_from_list"])
            return
        await state.update_data(reg_district=text)
        await state.set_state(RegStates.confirm_district)
        await message.answer(
            MESSAGES[lang]["confirm_district"].format(html_module.escape(text)),
            parse_mode="HTML",
            reply_markup=get_confirm_keyboard(lang),
        )
        return

    # ===== CONFIRM DISTRICT =====
    if current_state == RegStates.confirm_district:
        if text == yes_btn:
            data = await state.get_data()
            region_full = (
                f"{data.get('reg_region', '')}, {data.get('reg_district', '')}"
            )
            await update_or_create_user(uid, region=region_full)  # ← await qo'shildi
            await state.set_state(RegStates.phone)
            kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📞 Telefon yuborish", request_contact=True)]
                ],
                resize_keyboard=True,
            )
            await message.answer(MESSAGES[lang]["send_phone"], reply_markup=kb)
        elif text == no_btn:
            data = await state.get_data()
            region_name = data.get("reg_region", "")
            regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])
            districts = regions.get(region_name, [])
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=d)] for d in districts]
                + [[KeyboardButton(text=back_btn)]],
                resize_keyboard=True,
            )
            await state.set_state(RegStates.district)
            await message.answer(MESSAGES[lang]["choose_district"], reply_markup=kb)
        else:
            await message.answer(MESSAGES[lang]["choose_from_list"])
        return

    # ===== TEST-DRAYV: DEALER =====
    if current_state == TestDriveStates.choose_dealer:
        data = await state.get_data()
        dealers_map = data.get("td_dealers", {})
        if text not in dealers_map:
            await message.answer(MESSAGES[lang]["choose_from_list"])
            return
        await state.update_data(td_dealer_id=dealers_map[text], td_dealer_name=text)
        products_map = data.get("td_products", {})
        rows = [[KeyboardButton(text=p)] for p in products_map.keys()]
        rows.append([KeyboardButton(text=back_btn)])
        kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
        await state.set_state(TestDriveStates.choose_product)
        await message.answer(MESSAGES[lang]["td_choose_product"], reply_markup=kb)
        return

    # ===== TEST-DRAYV: PRODUCT =====
    if current_state == TestDriveStates.choose_product:
        data = await state.get_data()
        products_map = data.get("td_products", {})
        if text not in products_map:
            await message.answer(MESSAGES[lang]["choose_from_list"])
            return
        await state.update_data(td_product_id=products_map[text], td_product_name=text)
        await state.set_state(TestDriveStates.choose_date)
        await message.answer(
            MESSAGES[lang]["td_choose_date"], reply_markup=get_date_keyboard(back_btn)
        )
        return

    # ===== TEST-DRAYV: DATE =====
    if current_state == TestDriveStates.choose_date:
        try:
            parsed = datetime.strptime(text, "%d.%m.%Y").date()
            today = timezone.localtime(timezone.now()).date()
            if parsed < today or parsed > today + timedelta(days=14):
                await message.answer(MESSAGES[lang]["td_invalid_date"])
                return
        except ValueError:
            await message.answer(MESSAGES[lang]["td_invalid_date"])
            return
        await state.update_data(td_date=parsed, td_date_display=text)
        data = await state.get_data()
        time_slots = data.get("td_time_slots", [])
        rows = []
        row = []
        for ts in time_slots:
            row.append(KeyboardButton(text=ts))
            if len(row) == 3:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        rows.append([KeyboardButton(text=back_btn)])
        kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
        await state.set_state(TestDriveStates.choose_time)
        await message.answer(MESSAGES[lang]["td_choose_time"], reply_markup=kb)
        return

    # ===== TEST-DRAYV: TIME =====
    if current_state == TestDriveStates.choose_time:
        data = await state.get_data()
        time_slots = data.get("td_time_slots", [])
        if text not in time_slots:
            await message.answer(MESSAGES[lang]["choose_from_list"])
            return
        await state.update_data(td_time=text)

        user_data = await get_user_by_telegram_id(uid)  # ← await qo'shildi
        td_name = (user_data.first_name if user_data else None) or ""
        td_phone = (user_data.phone if user_data else None) or ""
        await state.update_data(td_name=td_name, td_phone=td_phone)

        data = await state.get_data()
        await state.set_state(TestDriveStates.confirm)
        confirm_text = MESSAGES[lang]["td_confirm"].format(
            dealer=html_module.escape(data.get("td_dealer_name", "")),
            product=html_module.escape(data.get("td_product_name", "")),
            date=html_module.escape(data.get("td_date_display", "")),
            time=html_module.escape(text),
            name=html_module.escape(td_name),
            phone=html_module.escape(td_phone),
        )
        await message.answer(
            confirm_text, parse_mode="HTML", reply_markup=get_confirm_keyboard(lang)
        )
        return

    # ===== TEST-DRAYV: CONFIRM =====
    if current_state == TestDriveStates.confirm:
        if text == yes_btn:
            data = await state.get_data()
            request_data = {
                "name": data.get("td_name"),
                "phone": data.get("td_phone"),
                "dealer_id": data.get("td_dealer_id"),  # ← ForeignKey uchun _id
                "product_id": data.get("td_product_id"),  # ← ForeignKey uchun _id
                "preferred_date": data.get("td_date"),
                "preferred_time": data.get("td_time"),
                "agree_terms": True,
            }
            test_drive_obj, error = await create_test_drive_request(
                request_data
            )  # ← await qo'shildi
            if test_drive_obj and not error:
                await message.answer(MESSAGES[lang]["td_success"])
            elif error == "daily_limit":
                await message.answer(MESSAGES[lang]["td_daily_limit"])
            else:
                await message.answer(MESSAGES[lang]["td_error"])
            await state.clear()
            await message.answer(
                MESSAGES[lang]["main_menu"],
                reply_markup=get_main_menu_keyboard(lang)
            )
        elif text == no_btn:
            await state.clear()
            await message.answer(
                MESSAGES[lang]["main_menu"], 
                reply_markup=get_main_menu_keyboard(lang)
            )
        else:
            await message.answer(MESSAGES[lang]["choose_from_list"])
        return


# ================= RUN =================


async def main():
    await bot.set_my_description(
        description=(
            "🇺🇿 Assalomu alaykum!\n"
            "Autoliga.uz rasmiy botiga xush kelibsiz! 🚗\n\n"
            "Bu bot orqali siz:\n"
            "🔹 Avtomobillar katalogini ko'rishingiz\n"
            "🔹 Har bir avto haqida batafsil ma'lumot olishingiz\n"
            "🔹 Dilerlik markazlari bilan tanishishingiz\n"
            "🔹 Test-drayvga yozilishingiz mumkin\n\n"
            "━━━━━━━━━━━━━━━\n\n"
            "🇷🇺 Здравствуйте!\n"
            "Добро пожаловать в официальный бот Autoliga.uz! 🚗\n\n"
            "Через этот бот вы можете:\n"
            "🔹 Просматривать каталог автомобилей\n"
            "🔹 Получать подробную информацию о каждом авто\n"
            "🔹 Ознакомиться с дилерскими центрами\n"
            "🔹 Записаться на тест-драйв"
        )
    )
    await dp.start_polling(bot, handle_signals=False)


if __name__ == "__main__":
    asyncio.run(main())