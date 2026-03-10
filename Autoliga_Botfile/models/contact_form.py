from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.sql import func
from database import Base
from datetime import datetime


class TelegramUser(Base):
    __tablename__ = "main_telegramuser"
    __table_args__ = {'extend_existing': True} 


    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)  
    first_name = Column(String(150), nullable=True)
    phone = Column(String(20), nullable=True)
    region = Column(String(200), nullable=True)
    language = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)  