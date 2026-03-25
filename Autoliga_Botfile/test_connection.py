"""
Django ORM orqali database ulanishini tekshirish.
Ishga tushirish: python test_connection.py
"""
import django
import os
import sys
from django.db import connection

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")



django.setup()
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    print("✅ PostgreSQL ulanish muvaffaqiyatli!")

    from main.models import (Dealer, Product, ProductCategory, TelegramUser,
                             TestDriveRequest)

    print(f"  TelegramUser: {TelegramUser.objects.count()} ta")
    print(f"  ProductCategory: {ProductCategory.objects.count()} ta")
    print(f"  Product: {Product.objects.count()} ta")
    print(f"  Dealer: {Dealer.objects.count()} ta")
    print(f"  TestDriveRequest: {TestDriveRequest.objects.count()} ta")

except Exception as e:
    print(f"❌ Ulanish xatosi: {e}")
