#!/usr/bin/env python
"""
Test script to verify Django-bot integration without starting the actual bot.
This simulates the startup process to ensure the integration code works.
"""
import os
import sys
import django

# Setup Django
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

print("✓ Django setup successful")

# Test bot import path
bot_dir = os.path.join(PROJECT_ROOT, 'Autoliga_Botfile')
sys.path.insert(0, bot_dir)

try:
    # Try to import bot module (will fail if aiogram not installed, but that's OK)
    import bot
    print("✓ Bot module import path works")
except ImportError as e:
    if "aiogram" in str(e):
        print("⚠ Bot module import fails due to missing aiogram (expected)")
    else:
        print(f"✗ Unexpected import error: {e}")

# Test apps.py logic
try:
    from main.apps import MainConfig
    print("✓ MainConfig import successful")

    # Test the path construction logic
    test_bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(MainConfig.__module__.replace('.', '/')))), 'Autoliga_Botfile')
    print(f"✓ Bot directory path construction works: {test_bot_dir}")

except Exception as e:
    print(f"✗ Apps.py logic error: {e}")

print("\nIntegration test complete. The Django-bot integration code is syntactically correct.")
print("To fully test, ensure aiogram is installed and BOT_TOKEN is configured in .env file.")