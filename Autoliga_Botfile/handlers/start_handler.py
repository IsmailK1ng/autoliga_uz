from aiogram import types
from database import SessionLocal
from models.user_model import User

async def start_handler(message: types.Message):
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    language = message.from_user.language_code

    session = SessionLocal()
    user = session.query(User).filter(User.telegram_id==telegram_id).first()
    if not user: # agar user no table
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            language=language
        )
        session.add(user)
        session.commit()
    session.close()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("Send my phone number", request_contact=True)
    keyboard.add(button)

    await message.answer(f"Hello {first_name}! Please send your phone number.", reply_markup=keyboard)


async def contact_handler(message: types.Message):
    if message.contact:
        phone = message.contact.phone_number
        telegram_id = message.from_user.id

        session = SessionLocal()
        user = session.query(User).filter(User.telegram_id==telegram_id).first()
        if user:
            user.phone = phone
            session.commit()
        session.close()

        await message.answer("✅ Your phone number has been saved!", reply_markup=types.ReplyKeyboardRemove())
