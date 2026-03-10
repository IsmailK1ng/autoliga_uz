from sqlalchemy import create_engine
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)

try:
    connection = engine.connect()
    print("✅ Connected to PostgreSQL!")
    connection.close()
except Exception as e:
    print("❌ Connection failed:", e)