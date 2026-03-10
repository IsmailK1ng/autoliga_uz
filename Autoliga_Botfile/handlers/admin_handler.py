from aiogram import types
from config import ADMIN_ID
from database import SessionLocal
from models.user_model import User

async def list_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ You are not admin!")

    session = SessionLocal()
    users = session.query(User).all()
    session.close()

    if not users:
        return await message.answer("No users found.")

    text = "📋 Users list:\n"
    for u in users:
        text += f"ID: {u.telegram_id}, Name: {u.first_name} {u.last_name}, Lang: {u.language}, Phone: {u.phone}\n"

    await message.answer(text)
