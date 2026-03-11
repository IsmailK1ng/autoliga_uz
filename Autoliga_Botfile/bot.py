from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile
import asyncio
import html as html_module
import os
import time
from database import Base, engine, SessionLocal
from models.contact_form import TelegramUser
from config import BOT_TOKEN, ADMIN_ID, MEDIA_ROOT
from sqlalchemy import text as sql_text

bot = Bot(token=BOT_TOKEN)


import re
def sanitize_name(text):
    if not isinstance(text, str):
        return None

    text = text.strip()

    if len(text) < 2:
        return None  

    if len(text) > 30:
        return None 

    if not re.fullmatch(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ\s\-]{2,30}", text):
        return None  # raqam, emoji yoki boshqa belgilar

    return text
# ================= DEALER REGION LABELS =================

DEALER_REGION_LABELS = {
    "uz": {
        "qoraqalpogiston":  "Qoraqalpog'iston Respublikasi",
        "xorazm":           "Xorazm viloyati",
        "buxoro":           "Buxoro viloyati",
        "navoiy":           "Navoiy viloyati",
        "samarqand":        "Samarqand viloyati",
        "qashqadaryo":      "Qashqadaryo viloyati",
        "surxondaryo":      "Surxondaryo viloyati",
        "jizzax":           "Jizzax viloyati",
        "sirdaryo":         "Sirdaryo viloyati",
        "toshkent-viloyati":"Toshkent viloyati",
        "toshkent-shahri":  "Toshkent shahri",
        "namangan":         "Namangan viloyati",
        "andijon":          "Andijon viloyati",
        "fargona":          "Farg'ona viloyati",
    },
    "ru": {
        "qoraqalpogiston":  "Республика Каракалпакстан",
        "xorazm":           "Хорезмская область",
        "buxoro":           "Бухарская область",
        "navoiy":           "Навоийская область",
        "samarqand":        "Самаркандская область",
        "qashqadaryo":      "Кашкадарьинская область",
        "surxondaryo":      "Сурхандарьинская область",
        "jizzax":           "Джизакская область",
        "sirdaryo":         "Сырдарьинская область",
        "toshkent-viloyati":"Ташкентская область",
        "toshkent-shahri":  "город Ташкент",
        "namangan":         "Наманганская область",
        "andijon":          "Андижанская область",
        "fargona":          "Ферганская область",
    },
}

# ================= REGIONS =================

UZ_REGIONS = {
    "uz": {
        "Toshkent shahri": ["Yunusobod", "Chilonzor", "Olmazor", "Yashnobod", "Mirzo Ulug'bek", "Sergeli", "Bektemir"],
        "Toshkent viloyati": ["Zangiota", "Chinoz", "Parkent", "Bo'ka", "Ohangaron", "Oqqo'rg'on", "Bekobod"],
        "Samarqand": ["Urgut", "Kattaqo'rg'on", "Bulung'ur", "Narpay", "Toyloq", "Qo'shrabot", "Ishtixon"],
        "Andijon": ["Asaka", "Shahrixon", "Xo'jaobod", "Qo'rg'ontepa", "Baliqchi", "Ulug'nor", "Oltinko'l", "Andijon"],
        "Farg'ona": ["Qo'qon", "Marg'ilon", "Farg'ona", "Oltiariq", "Beshariq", "Quva", "Rishton"],
        "Namangan": ["Chust", "Kosonsoy", "Namangan", "Pop", "To'raqo'rg'on", "Uychi", "Mingbuloq"],
        "Buxoro": ["G'ijduvon", "Kogon", "Buxoro", "Vobkent", "Peshku", "Romitan", "Shofirkon"],
        "Xorazm": ["Urganch", "Xiva", "Shovot", "Gurlan", "Yangiariq", "Bog'ot", "Xonqa"],
        "Qashqadaryo": ["Qarshi", "Shahrisabz", "G'uzor", "Chiroqchi", "Koson", "Kitob", "Dehqonobod"],
        "Surxondaryo": ["Termiz", "Denov", "Boysun", "Muzrabot", "Sariosiyo", "Qumqo'rg'on", "Sherobod"],
        "Jizzax": ["Zomin", "G'allaorol", "Zarbdor", "Do'stlik", "Yangiobod", "Arnasoy", "Baxmal"],
        "Sirdaryo": ["Guliston", "Yangiyer", "Sirdaryo", "Oqoltin", "Shirin", "Boyovut"],
        "Navoiy": ["Zarafshon", "Karmana", "Navoiy", "Qiziltepa", "Tomdi", "Xatirchi", "Konimex"],
        "Qoraqalpog'iston": ["Nukus", "Xo'jayli", "Kegeyli", "Chimboy", "Taxtako'pir", "Beruniy", "Qo'ng'irot"],
    },
    "ru": {
        "Ташкент (город)": ["Юнусабад", "Чиланзар", "Олмазар", "Яшнабад", "Мирзо-Улугбек", "Сергели", "Бектемир"],
        "Ташкентская область": ["Зангиата", "Чиноз", "Паркент", "Бука", "Ахангаран", "Аккурган", "Бекабад"],
        "Самарканд": ["Ургут", "Каттакурган", "Булунгур", "Нарпай", "Тайлак", "Кошрабад", "Иштихон"],
        "Андижан": ["Асака", "Шахрихан", "Ходжаабад", "Курганtepa", "Балыкчи", "Улугнор", "Алтынкуль", "Андижан"],
        "Фергана": ["Коканд", "Маргилан", "Фергана", "Олтиарик", "Бешарик", "Кува", "Риштан"],
        "Наманган": ["Чуст", "Косонсой", "Наманган", "Поп", "Туракурган", "Уйчи", "Мингбулак"],
        "Бухара": ["Гиждуван", "Коган", "Бухара", "Вабкент", "Пешку", "Ромитан", "Шафиркан"],
        "Хорезм": ["Ургенч", "Хива", "Шават", "Гурлан", "Янгиарик", "Богот", "Ханка"],
        "Кашкадарья": ["Карши", "Шахрисабз", "Гузар", "Чирокчи", "Касан", "Китаб", "Дехканабад"],
        "Сурхандарья": ["Термез", "Денов", "Байсун", "Музрабад", "Сариосиё", "Кумкурган", "Шерабад"],
        "Джизак": ["Зомин", "Галляарал", "Зарбдар", "Дустлик", "Янгиобод", "Арнасай", "Бахмал"],
        "Сырдарья": ["Гулистан", "Янгиер", "Сырдарья", "Акалтын", "Ширин", "Баяут"],
        "Навои": ["Зарафшан", "Кармана", "Навои", "Кызылтепа", "Томди", "Хатирчи", "Конимех"],
        "Каракалпакстан": ["Нукус", "Ходжейли", "Кегейли", "Чимбай", "Тахиаташ", "Беруний", "Кунград"],
    }
}

# ================= FSM STATES =================

class RegStates(StatesGroup):
    first_name = State()
    age = State()
    region = State()
    district = State()
    phone = State()

class NavStates(StatesGroup):
    choose_brand = State()
    choose_car = State()

# ================= KEYBOARDS =================

LANG_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")]
    ],
    resize_keyboard=True
)

ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Foydalanuvchilar ro'yxati")],
        [KeyboardButton(text="📊 Statistika")],
    ],
    resize_keyboard=True
)

MESSAGES = {
    "uz": {
        "choose_lang": "Tilni tanlang 🌐",
        "send_phone": "Telefoningizni yuboring 📞",
        "send_first_name": "Ismingizni kiriting",
        "send_age": "Yoshingizni kiriting (masalan: 25)",
        "wrong_age": "Yosh noto'g'ri ❌\nFaqat raqam kiriting",
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
    },
    "ru": {
        "choose_lang": "Выберите язык 🌐",
        "send_phone": "Отправьте ваш номер телефона 📞",
        "send_first_name": "Введите имя",
        "send_age": "Введите ваш возраст (например: 25)",
        "wrong_age": "Неверный возраст ❌\nВведите только цифры",
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
    }
}

CHANGE_LANG_BTNS = {MESSAGES["uz"]["change_lang_btn"], MESSAGES["ru"]["change_lang_btn"]}


def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    if lang == "ru":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚗 Автомобили"), KeyboardButton(text="🏢 Дилерские центры")],
                [KeyboardButton(text=MESSAGES["ru"]["change_lang_btn"])],
            ],
            resize_keyboard=True
        )
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚗 Mashinalar"), KeyboardButton(text="🏢 Dilerlik markazlari")],
            [KeyboardButton(text=MESSAGES["uz"]["change_lang_btn"])],
        ],
        resize_keyboard=True
    )

# ================= INIT =================

Base.metadata.create_all(bind=engine)

dp = Dispatcher(storage=MemoryStorage())

# Foydalanuvchi tili: tezkor lookup uchun xotirada saqlanadi (DB dan yuklanadi)
user_lang: dict = {}

# ================= LANG SAFETY =================

ALLOWED_LANGS = {"uz", "ru"}

def _safe_lang(lang: str) -> str:
    """SQL injection oldini olish: faqat ruxsat etilgan til kodlari."""
    return lang if lang in ALLOWED_LANGS else "uz"

# ================= CACHE =================

_brands_cache: dict = {}
BRANDS_CACHE_TTL = 60  # sekund

# ================= DB HELPERS =================

def _coalesce(primary, fallback):
    return primary if primary else fallback


def db_get_brands(lang: str = "uz"):
    lang = _safe_lang(lang)
    now = time.monotonic()
    cached = _brands_cache.get(lang)
    if cached and now - cached["ts"] < BRANDS_CACHE_TTL:
        return cached["data"]
    db = SessionLocal()
    try:
        rows = db.execute(sql_text(
            f'SELECT id, name_{lang}, name FROM main_productcategory '
            'WHERE is_active = TRUE ORDER BY "order", name'
        )).fetchall()
        result = [{"id": r[0], "name": _coalesce(r[1], r[2])} for r in rows]
        _brands_cache[lang] = {"data": result, "ts": now}
        return result
    except Exception:
        return []
    finally:
        db.close()


def db_get_cars(brand_id: int, lang: str = "uz"):
    lang = _safe_lang(lang)
    db = SessionLocal()
    try:
        rows = db.execute(sql_text(
            f'SELECT id, title_{lang}, title FROM main_product '
            'WHERE category_id = :cid AND is_active = TRUE ORDER BY "order", title'
        ), {"cid": brand_id}).fetchall()
        return [{"id": r[0], "title": _coalesce(r[1], r[2])} for r in rows]
    except Exception:
        return []
    finally:
        db.close()


def db_get_dealers(lang: str = "uz"):
    lang = _safe_lang(lang)
    db = SessionLocal()
    try:
        rows = db.execute(sql_text(
            f'SELECT name_{lang}, name, region, address_{lang}, address, phone, working_hours_{lang}, working_hours '
            'FROM main_dealer WHERE is_active = TRUE ORDER BY "order", name'
        )).fetchall()
        return [
            {
                "name":    _coalesce(r[0], r[1]),
                "region":  r[2],
                "address": _coalesce(r[3], r[4]),
                "phone":   r[5],
                "hours":   _coalesce(r[6], r[7]),
            }
            for r in rows
        ]
    except Exception:
        return []
    finally:
        db.close()


def db_get_car_detail(car_id: int, lang: str = "uz"):
    lang = _safe_lang(lang)
    db = SessionLocal()
    try:
        car = db.execute(sql_text(
            f"SELECT title_{lang}, title, main_image, card_image, "
            f"slider_price_{lang}, slider_price, slider_year, "
            f"slider_power_{lang}, slider_power, "
            f"slider_fuel_consumption_{lang}, slider_fuel_consumption "
            "FROM main_product WHERE id = :id"
        ), {"id": car_id}).fetchone()
        if not car:
            return None

        features = db.execute(sql_text(
            f'SELECT name_{lang}, name FROM main_productfeature '
            'WHERE product_id = :id ORDER BY "order" LIMIT 6'
        ), {"id": car_id}).fetchall()

        return {
            "title": _coalesce(car[0], car[1]),
            "main_image": car[2],
            "card_image": car[3],
            "price": _coalesce(car[4], car[5]),
            "year": car[6],
            "power": _coalesce(car[7], car[8]),
            "fuel": _coalesce(car[9], car[10]),
            "features": [_coalesce(f[0], f[1]) for f in features],
        }
    except Exception:
        return None
    finally:
        db.close()


def build_car_caption(car: dict, lang: str) -> str:
    lines = [f"<b>{html_module.escape(car['title'])}</b>"]
    if car.get("year"):
        lines.append(f"📅 {html_module.escape(str(car['year']))}")
    if car.get("price"):
        lines.append(f"💰 {html_module.escape(str(car['price']))}")
    if car.get("power"):
        lines.append(f"⚡ {html_module.escape(str(car['power']))}")
    if car.get("fuel"):
        lines.append(f"⛽ {html_module.escape(str(car['fuel']))}")
    if car.get("features"):
        lines.append("")
        for feat in car["features"]:
            lines.append(f"• {html_module.escape(feat)}")
    return "\n".join(lines)


def get_image_path(relative_path: str) -> str | None:
    if not relative_path:
        return None
    safe_path = os.path.normpath(relative_path).lstrip("/\\")
    full_path = os.path.join(MEDIA_ROOT, safe_path)
    if not full_path.startswith(os.path.abspath(MEDIA_ROOT)):
        return None
    return full_path if os.path.exists(full_path) else None



# ================= MEDIA BLOCKER =================

@dp.message(~F.text & ~F.contact)
async def block_unsupported_media(message: types.Message):
    lang = user_lang.get(message.from_user.id, "uz")
    await message.answer(MESSAGES[lang]["unsupported"])

# ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    db = SessionLocal()
    try:
        user = db.query(TelegramUser).filter(TelegramUser.telegram_id == message.from_user.id).first()
        has_profile = bool(user and user.phone and user.first_name)
        lang = (user.language or "uz") if user else "uz"
    finally:
        db.close()

    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Admin panel", reply_markup=ADMIN_KEYBOARD)
        return

    if not has_profile:
        await state.clear()
        await message.answer(MESSAGES["uz"]["choose_lang"], reply_markup=LANG_KEYBOARD)
    else:
        user_lang[message.from_user.id] = lang
        await state.clear()
        await message.answer(MESSAGES[lang]["welcome_back"], reply_markup=get_main_menu_keyboard(lang))


# ================= TIL O'ZGARTIRISH (asosiy menyudan) =================

@dp.message(F.text.in_(CHANGE_LANG_BTNS))
async def request_lang_change(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        MESSAGES["uz"]["choose_lang"] + " / " + MESSAGES["ru"]["choose_lang"],
        reply_markup=LANG_KEYBOARD
    )


# ================= LANGUAGE (ro'yxatdan o'tish va til o'zgartirish) =================

@dp.message(F.text.startswith("🇺🇿") | F.text.startswith("🇷🇺"))
async def choose_language(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    lang = "uz" if message.text.startswith("🇺🇿") else "ru"
    user_lang[uid] = lang

    db = SessionLocal()
    try:
        user = db.query(TelegramUser).filter(TelegramUser.telegram_id == uid).first()
        if not user:
            user = TelegramUser(telegram_id=uid)
            db.add(user)
        user.language = lang
        user.username = message.from_user.username
        db.commit()
        has_profile = bool(user.phone and user.first_name)
    finally:
        db.close()

    if has_profile:
        await state.clear()
        await message.answer(MESSAGES[lang]["lang_changed"], reply_markup=get_main_menu_keyboard(lang))
    else:
        await state.set_state(RegStates.first_name)
        await message.answer(MESSAGES[lang]["send_first_name"], reply_markup=ReplyKeyboardRemove())


# ================= CONTACT =================

@dp.message(F.contact)
async def save_phone(message: types.Message, state: FSMContext):
    lang = user_lang.get(message.from_user.id, "uz")

    if message.contact.user_id != message.from_user.id:
        await message.answer("❌")
        return

    db = SessionLocal()
    try:
        user = db.query(TelegramUser).filter(TelegramUser.telegram_id == message.from_user.id).first()
        if not user:
            return
        user.phone = message.contact.phone_number
        db.commit()
    finally:
        db.close()

    await state.clear()
    await message.answer(
        MESSAGES[lang]["saved"] + "\n\n" + MESSAGES[lang]["main_menu"],
        reply_markup=get_main_menu_keyboard(lang)
    )


# ================= ADMIN PANEL =================

@dp.message(F.text == "📋 Foydalanuvchilar ro'yxati", F.from_user.id == ADMIN_ID)
async def show_users(message: types.Message):
    db = SessionLocal()
    try:
        users = db.query(TelegramUser).all()
        # ORM obyektlari session yopilgandan keyin ham ishlaydi (eager load)
        user_cards = [
            (
                u.telegram_id,
                u.first_name or "-",
                u.age,
                u.phone or "-",
                u.language or "-",
                u.region or "-",
            )
            for u in users
        ]
    finally:
        db.close()

    if not user_cards:
        await message.answer("Foydalanuvchilar yo'q ❌")
        return

    chunks = []
    current = f"📋 <b>Foydalanuvchilar ro'yxati</b> — jami: {len(user_cards)} ta\n\n"

    for i, (tg_id, fname, age, phone, language, region) in enumerate(user_cards, 1):
        card = (
            f"<b>#{i}</b> | 🆔 <code>{tg_id}</code>\n"
            f"👤 {html_module.escape(fname)}   🎂 {age or '-'}\n"
            f"📞 {html_module.escape(phone)}\n"
            f"🌍 {language}   🏙 {html_module.escape(region)}\n"
            f"━━━━━━━━━━━━━━━\n"
        )
        if len(current) + len(card) > 4000:
            chunks.append(current)
            current = card
        else:
            current += card

    if current:
        chunks.append(current)

    for chunk in chunks:
        await message.answer(chunk, parse_mode="HTML")


@dp.message(F.text == "📊 Statistika", F.from_user.id == ADMIN_ID)
async def show_stats(message: types.Message):
    db = SessionLocal()
    try:
        users = db.query(TelegramUser).all()
        stats = [
            (u.language, bool(u.phone), bool(u.phone and u.first_name and u.region), u.region)
            for u in users
        ]
    finally:
        db.close()

    total = len(stats)
    uz_count = sum(1 for s in stats if s[0] == "uz")
    ru_count = sum(1 for s in stats if s[0] == "ru")
    with_phone = sum(1 for s in stats if s[1])
    complete = sum(1 for s in stats if s[2])

    region_counts: dict = {}
    for s in stats:
        if s[3]:
            base = s[3].split(",")[0].strip()
            region_counts[base] = region_counts.get(base, 0) + 1
    top_regions = sorted(region_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    text = (
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total}</b>\n"
        f"✅ Ro'yxatdan to'liq o'tganlar: <b>{complete}</b>\n"
        f"📞 Telefon berganlar: <b>{with_phone}</b>\n\n"
        f"🌐 Tillar:\n"
        f"   🇺🇿 O'zbekcha: <b>{uz_count}</b>\n"
        f"   🇷🇺 Ruscha: <b>{ru_count}</b>\n"
    )
    if top_regions:
        text += "\n🏙 Top viloyatlar:\n"
        for region, count in top_regions:
            text += f"   • {html_module.escape(region)}: <b>{count}</b>\n"

    await message.answer(text, parse_mode="HTML")


# ================= MAIN MENU HANDLERS =================

@dp.message(F.text.in_({"🚗 Mashinalar", "🚗 Автомобили"}))
async def show_brands(message: types.Message, state: FSMContext):
    lang = user_lang.get(message.from_user.id, "uz")
    brands = db_get_brands(lang)

    if not brands:
        await message.answer(MESSAGES[lang]["no_cars"])
        return

    await state.set_state(NavStates.choose_brand)
    await state.update_data(brands={b["name"]: b["id"] for b in brands})

    rows = [[KeyboardButton(text=b["name"])] for b in brands]
    rows.append([KeyboardButton(text=MESSAGES[lang]["back_btn"])])
    kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
    await message.answer(MESSAGES[lang]["choose_brand"], reply_markup=kb)


@dp.message(F.text.in_({"🏢 Dilerlik markazlari", "🏢 Дилерские центры"}))
async def show_dealers(message: types.Message):
    lang = user_lang.get(message.from_user.id, "uz")
    dealers = db_get_dealers(lang)

    if not dealers:
        await message.answer(MESSAGES[lang]["dealers_title"])
        return

    header = "🏢 <b>Dilerlik markazlari:</b>\n\n" if lang == "uz" else "🏢 <b>Дилерские центры:</b>\n\n"
    lines = []
    for d in dealers:
        block = f"<b>{html_module.escape(d['name'])}</b>"
        if d['region']:
            region_label = DEALER_REGION_LABELS.get(lang, {}).get(d['region'], d['region'])
            block += f"\n📍 {html_module.escape(region_label)}"
        if d['address']:
            block += f"\n🏠 {html_module.escape(d['address'])}"
        if d['phone']:
            block += f"\n📞 {html_module.escape(d['phone'])}"
        if d['hours']:
            block += f"\n🕐 {html_module.escape(d['hours'])}"
        lines.append(block)

    text = header + "\n\n".join(lines)
    await message.answer(text, parse_mode="HTML")


# ================= CATCH-ALL: registration + navigation states =================

@dp.message()
async def register_process(message: types.Message, state: FSMContext):

    uid = message.from_user.id
    current_state = await state.get_state()
    lang = user_lang.get(uid, "uz")
    back_btn = MESSAGES[lang]["back_btn"]

    # media bloklash
    if not message.text:
        await message.answer(MESSAGES[lang]["unsupported"])
        return

    text = message.text.strip()




    
    # ---- BACK button ----
    if text == back_btn:
        if current_state == NavStates.choose_brand:
            await state.clear()
            await message.answer(MESSAGES[lang]["main_menu"], reply_markup=get_main_menu_keyboard(lang))

        elif current_state == NavStates.choose_car:
            brands = db_get_brands(lang)

            await state.set_state(NavStates.choose_brand)
            await state.update_data(brands={b["name"]: b["id"] for b in brands})

            rows = [[KeyboardButton(text=b["name"])] for b in brands]
            rows.append([KeyboardButton(text=back_btn)])

            kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

            await message.answer(MESSAGES[lang]["choose_brand"], reply_markup=kb)

        else:
            await state.clear()
            await message.answer(MESSAGES[lang]["main_menu"], reply_markup=get_main_menu_keyboard(lang))

        return

    # ---- BRAND selection ----
    if current_state == NavStates.choose_brand:

        data = await state.get_data()
        brands_map = data.get("brands", {})

        if text not in brands_map:
            await message.answer(MESSAGES[lang]["choose_from_list"])
            return

        brand_id = brands_map[text]

        cars = db_get_cars(brand_id, lang)

        if not cars:
            await message.answer(MESSAGES[lang]["no_cars"])
            return

        await state.set_state(NavStates.choose_car)

        await state.update_data(
            brands=brands_map,
            brand_id=brand_id,
            brand_name=text,
            cars={c["title"]: c["id"] for c in cars},
        )

        rows = [[KeyboardButton(text=c["title"])] for c in cars]
        rows.append([KeyboardButton(text=back_btn)])

        kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

        await message.answer(
            f"{html_module.escape(text)} — {MESSAGES[lang]['choose_model']}",
            reply_markup=kb
        )

        return

    # ---- CAR selection ----
    if current_state == NavStates.choose_car:

        data = await state.get_data()
        cars_map = data.get("cars", {})

        if text not in cars_map:
            await message.answer(MESSAGES[lang]["choose_from_list"])
            return

        car_id = cars_map[text]

        car = db_get_car_detail(car_id, lang)

        if not car:
            await message.answer("❌")
            return

        caption = build_car_caption(car, lang)

        image_path = get_image_path(car["card_image"] or car["main_image"])

        if image_path:
            await message.answer_photo(
                photo=FSInputFile(image_path),
                caption=caption,
                parse_mode="HTML"
            )
        else:
            await message.answer(caption, parse_mode="HTML")

        return

    # ---- REGISTRATION flow ----
    db = SessionLocal()

    try:

        user = db.query(TelegramUser).filter(TelegramUser.telegram_id == uid).first()

        if not user:
            return

        # ---- FIRST NAME ----
        if current_state == RegStates.first_name:

            name = sanitize_name(message.text)

           
            if not name:
                await message.answer(MESSAGES[lang]["invalid_name"])
                return

            user.first_name = name
            db.commit()

            await state.set_state(RegStates.age)
            await message.answer(MESSAGES[lang]["send_age"])

        # ---- AGE ----
        elif current_state == RegStates.age:

            if text.isdigit() and 5 <= int(text) <= 100:

                user.age = int(text)
                db.commit()

                await state.set_state(RegStates.region)

                regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])

                region_kb = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text=r)] for r in regions.keys()],
                    resize_keyboard=True
                )

                await message.answer(MESSAGES[lang]["choose_region"], reply_markup=region_kb)

            else:
                await message.answer(MESSAGES[lang]["wrong_age"])


        # ---- REGION ----
        elif current_state == RegStates.region:

            regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])

            if text in regions:

                user.region = text
                db.commit()

                districts = regions[text]

                district_kb = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text=d)] for d in districts],
                    resize_keyboard=True
                )

                await state.set_state(RegStates.district)

                await message.answer(MESSAGES[lang]["choose_district"], reply_markup=district_kb)

            else:
                await message.answer(MESSAGES[lang]["choose_from_list"])


        # ---- DISTRICT ----
        elif current_state == RegStates.district:

            regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])

            region_name = (user.region or "").split(",")[0].strip()

            valid_districts = regions.get(region_name, [])

            if text not in valid_districts:
                await message.answer(MESSAGES[lang]["choose_from_list"])
                return

            user.region = f"{user.region}, {text}"
            db.commit()

            await state.set_state(RegStates.phone)

            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📞 Telefon yuborish", request_contact=True)]],
                resize_keyboard=True
            )

            await message.answer(MESSAGES[lang]["send_phone"], reply_markup=kb)

    finally:
        db.close()

# ================= RUN =================

async def main():
    await bot.set_my_description(
        description=(
            "🇺🇿 Assalomu alaykum!\n"
            "Autoliga.uz rasmiy botiga xush kelibsiz! 🚗\n\n"
            "Bu bot orqali siz:\n"
            "🔹 Avtomobillar katalogini ko'rishingiz\n"
            "🔹 Har bir avto haqida batafsil ma'lumot olishingiz\n"
            "🔹 Dilerlik markazlari bilan tanishishingiz mumkin\n\n"
            "━━━━━━━━━━━━━━━\n\n"
            "🇷🇺 Здравствуйте!\n"
            "Добро пожаловать в официальный бот Autoliga.uz! 🚗\n\n"
            "Через этот бот вы можете:\n"
            "🔹 Просматривать каталог автомобилей\n"
            "🔹 Получать подробную информацию о каждом авто\n"
            "🔹 Ознакомиться с дилерскими центрами"
        )
    )
    await dp.start_polling(bot, handle_signals=False)


if __name__ == "__main__":
    asyncio.run(main())
