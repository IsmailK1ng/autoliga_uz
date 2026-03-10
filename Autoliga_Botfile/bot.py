from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile
import asyncio
import os
from database import Base, engine, SessionLocal
from models.contact_form import TelegramUser
from config import BOT_TOKEN, ADMIN_ID, MEDIA_ROOT
from sqlalchemy import text as sql_text

bot = Bot(token=BOT_TOKEN)

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
    }
}


def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    if lang == "ru":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚗 Автомобили"), KeyboardButton(text="🏢 Дилерские центры")]
            ],
            resize_keyboard=True
        )
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚗 Mashinalar"), KeyboardButton(text="🏢 Dilerlik markazlari")]
        ],
        resize_keyboard=True
    )

# ================= INIT =================

Base.metadata.create_all(bind=engine)

dp = Dispatcher()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

user_state = {}
user_lang = {}
user_data = {}  # stores extra context: brand_id, brand_name, car list

# ================= DB HELPERS =================

def db_get_brands():
    db = next(get_db())
    try:
        rows = db.execute(sql_text(
            'SELECT id, name FROM main_productcategory '
            'WHERE is_active = TRUE ORDER BY "order", name'
        )).fetchall()
        return [{"id": r[0], "name": r[1]} for r in rows]
    except Exception:
        return []

def db_get_cars(brand_id: int):
    db = next(get_db())
    try:
        rows = db.execute(sql_text(
            'SELECT id, title FROM main_product '
            'WHERE category_id = :cid AND is_active = TRUE ORDER BY "order", title'
        ), {"cid": brand_id}).fetchall()
        return [{"id": r[0], "title": r[1]} for r in rows]
    except Exception:
        return []

def db_get_car_detail(car_id: int):
    db = next(get_db())
    try:
        car = db.execute(sql_text(
            "SELECT title, main_image, card_image, slider_price, slider_year, "
            "slider_power, slider_fuel_consumption "
            "FROM main_product WHERE id = :id"
        ), {"id": car_id}).fetchone()
        if not car:
            return None

        features = db.execute(sql_text(
            'SELECT name FROM main_productfeature '
            'WHERE product_id = :id ORDER BY "order" LIMIT 6'
        ), {"id": car_id}).fetchall()

        return {
            "title": car[0],
            "main_image": car[1],
            "card_image": car[2],
            "price": car[3],
            "year": car[4],
            "power": car[5],
            "fuel": car[6],
            "features": [f[0] for f in features],
        }
    except Exception:
        return None

def build_car_caption(car: dict, lang: str) -> str:
    lines = [f"<b>{car['title']}</b>"]
    if car.get("year"):
        lines.append(f"📅 {car['year']}")
    if car.get("price"):
        lines.append(f"💰 {car['price']}")
    if car.get("power"):
        lines.append(f"⚡ {car['power']}")
    if car.get("fuel"):
        lines.append(f"⛽ {car['fuel']}")
    if car.get("features"):
        lines.append("")
        for feat in car["features"]:
            lines.append(f"• {feat}")
    return "\n".join(lines)

def get_image_path(relative_path: str) -> str | None:
    if not relative_path:
        return None
    full_path = os.path.join(MEDIA_ROOT, relative_path)
    return full_path if os.path.exists(full_path) else None

# ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message):
    db = next(get_db())
    user = db.query(TelegramUser).filter(TelegramUser.telegram_id == message.from_user.id).first()

    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Admin panel", reply_markup=ADMIN_KEYBOARD)
        return

    if not user:
        user_state[message.from_user.id] = "lang"
        await message.answer(MESSAGES["uz"]["choose_lang"], reply_markup=LANG_KEYBOARD)
    else:
        lang = user.language or "uz"
        user_lang[message.from_user.id] = lang
        user_state.pop(message.from_user.id, None)
        await message.answer(MESSAGES[lang]["welcome_back"], reply_markup=get_main_menu_keyboard(lang))


# LANGUAGE
@dp.message(F.text.startswith("🇺🇿") | F.text.startswith("🇷🇺"))
async def choose_language(message: types.Message):
    db = next(get_db())
    lang = "uz" if message.text.startswith("🇺🇿") else "ru"
    user_lang[message.from_user.id] = lang

    user = db.query(TelegramUser).filter(TelegramUser.telegram_id == message.from_user.id).first()
    if not user:
        user = TelegramUser(telegram_id=message.from_user.id)
        db.add(user)

    user.language = lang
    user.username = message.from_user.username
    db.commit()
    user_state[message.from_user.id] = "first_name"

    await message.answer(MESSAGES[lang]["send_first_name"], reply_markup=ReplyKeyboardRemove())


# CONTACT — телефон собирается последним шагом регистрации
@dp.message(F.contact)
async def save_phone(message: types.Message):
    db = next(get_db())
    lang = user_lang.get(message.from_user.id, "uz")

    if message.contact.user_id != message.from_user.id:
        await message.answer("❌")
        return

    user = db.query(TelegramUser).filter(TelegramUser.telegram_id == message.from_user.id).first()
    user.phone = message.contact.phone_number
    db.commit()

    user_state.pop(message.from_user.id, None)
    await message.answer(
        MESSAGES[lang]["saved"] + "\n\n" + MESSAGES[lang]["main_menu"],
        reply_markup=get_main_menu_keyboard(lang)
    )


# ================= ADMIN PANEL =================

@dp.message(F.text == "📋 Foydalanuvchilar ro'yxati", F.from_user.id == ADMIN_ID)
async def show_users(message: types.Message):
    db = next(get_db())
    users = db.query(TelegramUser).all()

    if not users:
        await message.answer("Foydalanuvchilar yo'q ❌")
        return

    chunks = []
    current = f"📋 <b>Foydalanuvchilar ro'yxati</b> — jami: {len(users)} ta\n\n"

    for i, user in enumerate(users, 1):
        card = (
            f"<b>#{i}</b> | 🆔 <code>{user.telegram_id}</code>\n"
            f"👤 {user.first_name or '-'}   🎂 {user.age or '-'}\n"
            f"📞 {user.phone or '-'}\n"
            f"🌍 {user.language or '-'}   🏙 {user.region or '-'}\n"
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
    db = next(get_db())
    users = db.query(TelegramUser).all()

    total = len(users)
    uz_count = sum(1 for u in users if u.language == "uz")
    ru_count = sum(1 for u in users if u.language == "ru")
    with_phone = sum(1 for u in users if u.phone)
    complete = sum(1 for u in users if u.phone and u.first_name and u.region)

    region_counts = {}
    for u in users:
        if u.region:
            base = u.region.split(",")[0].strip()
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
            text += f"   • {region}: <b>{count}</b>\n"

    await message.answer(text, parse_mode="HTML")


# ================= MAIN MENU HANDLERS =================

@dp.message(F.text.in_({"🚗 Mashinalar", "🚗 Автомобили"}))
async def show_brands(message: types.Message):
    lang = user_lang.get(message.from_user.id, "uz")
    brands = db_get_brands()

    if not brands:
        await message.answer(MESSAGES[lang]["no_cars"])
        return

    user_data[message.from_user.id] = {"brands": {b["name"]: b["id"] for b in brands}}
    user_state[message.from_user.id] = "choose_brand"

    rows = [[KeyboardButton(text=b["name"])] for b in brands]
    rows.append([KeyboardButton(text=MESSAGES[lang]["back_btn"])])
    kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
    await message.answer(MESSAGES[lang]["choose_brand"], reply_markup=kb)


@dp.message(F.text.in_({"🏢 Dilerlik markazlari", "🏢 Дилерские центры"}))
async def show_dealers(message: types.Message):
    lang = user_lang.get(message.from_user.id, "uz")
    await message.answer(MESSAGES[lang]["dealers_title"])


# ================= CATCH-ALL: registration + navigation states =================

@dp.message()
async def register_process(message: types.Message):
    db = next(get_db())
    uid = message.from_user.id
    user = db.query(TelegramUser).filter(TelegramUser.telegram_id == uid).first()
    state = user_state.get(uid)
    lang = user_lang.get(uid, "uz")
    back_btn = MESSAGES[lang]["back_btn"]

    # ---- BACK button ----
    if message.text == back_btn:
        if state == "choose_brand":
            user_state.pop(uid, None)
            await message.answer(MESSAGES[lang]["main_menu"], reply_markup=get_main_menu_keyboard(lang))
        elif state == "choose_car":
            # Go back to brands
            brands = db_get_brands()
            user_data[uid] = {"brands": {b["name"]: b["id"] for b in brands}}
            user_state[uid] = "choose_brand"
            rows = [[KeyboardButton(text=b["name"])] for b in brands]
            rows.append([KeyboardButton(text=back_btn)])
            kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
            await message.answer(MESSAGES[lang]["choose_brand"], reply_markup=kb)
        else:
            user_state.pop(uid, None)
            await message.answer(MESSAGES[lang]["main_menu"], reply_markup=get_main_menu_keyboard(lang))
        return

    # ---- BRAND selection ----
    if state == "choose_brand":
        brands_map = user_data.get(uid, {}).get("brands", {})
        if message.text not in brands_map:
            await message.answer(MESSAGES[lang]["choose_from_list"])
            return

        brand_id = brands_map[message.text]
        cars = db_get_cars(brand_id)
        if not cars:
            await message.answer(MESSAGES[lang]["no_cars"])
            return

        user_data[uid] = {
            "brands": brands_map,
            "brand_id": brand_id,
            "brand_name": message.text,
            "cars": {c["title"]: c["id"] for c in cars},
        }
        user_state[uid] = "choose_car"

        rows = [[KeyboardButton(text=c["title"])] for c in cars]
        rows.append([KeyboardButton(text=back_btn)])
        kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
        await message.answer(
            f"{message.text} — {MESSAGES[lang]['choose_model']}",
            reply_markup=kb
        )
        return

    # ---- CAR selection ----
    if state == "choose_car":
        cars_map = user_data.get(uid, {}).get("cars", {})
        if message.text not in cars_map:
            await message.answer(MESSAGES[lang]["choose_from_list"])
            return

        car_id = cars_map[message.text]
        car = db_get_car_detail(car_id)
        if not car:
            await message.answer("❌")
            return

        caption = build_car_caption(car, lang)

        # Try to send with photo
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
    if not user:
        return

    if state == "first_name":
        user.first_name = message.text
        db.commit()
        user_state[uid] = "age"
        await message.answer(MESSAGES[lang]["send_age"])

    elif state == "age":
        if message.text.isdigit() and 5 <= int(message.text) <= 100:
            user.age = int(message.text)
            db.commit()
            user_state[uid] = "region"
            regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])
            region_kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=r)] for r in regions.keys()],
                resize_keyboard=True
            )
            await message.answer(MESSAGES[lang]["choose_region"], reply_markup=region_kb)
        else:
            await message.answer(MESSAGES[lang]["wrong_age"])

    elif state == "region":
        regions = UZ_REGIONS.get(lang, UZ_REGIONS["uz"])
        if message.text in regions:
            user.region = message.text
            db.commit()
            districts = regions[message.text]
            district_kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=d)] for d in districts],
                resize_keyboard=True
            )
            user_state[uid] = "district"
            await message.answer(MESSAGES[lang]["choose_district"], reply_markup=district_kb)
        else:
            await message.answer(MESSAGES[lang]["choose_from_list"])

    elif state == "district":
        user.region = f"{user.region}, {message.text}"
        db.commit()
        user_state[uid] = "phone"
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📞 Telefon yuborish", request_contact=True)]],
            resize_keyboard=True
        )
        await message.answer(MESSAGES[lang]["send_phone"], reply_markup=kb)


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
