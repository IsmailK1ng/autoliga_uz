from django.apps import AppConfig
import threading
import os
import logging

logger = logging.getLogger(__name__)


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import main.admin
        import main.signals

        import sys

        is_runserver = 'runserver' in sys.argv
        is_noreload = '--noreload' in sys.argv
        run_main = os.environ.get('RUN_MAIN')

        # Skip bot startup in auto-reloader parent process only.
        # With auto-reload: Django sets RUN_MAIN='true' in the worker child process.
        # With --noreload: RUN_MAIN is never set, but we still want to start the bot.
        if is_runserver and not is_noreload and run_main != 'true':
            return

        # Also skip for management commands (migrate, shell, etc.)
        if not is_runserver:
            return

        def start_bot():
            """Start the Telegram bot in a separate thread with proper error handling"""
            try:
                import asyncio

                # Add bot directory to Python path
                bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Autoliga_Botfile')
                if bot_dir not in sys.path:
                    sys.path.insert(0, bot_dir)

                # Prevent bot.py from calling django.setup() again (already set up)
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

                # Import bot's main function
                from bot import main as bot_main

                # Create new event loop for the bot to avoid conflicts with Django's async code
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                logger.info("Starting Telegram bot...")
                loop.run_until_complete(bot_main())

            except Exception as e:
                logger.error(f"Telegram bot crashed: {e}", exc_info=True)

        # Start bot in a daemon thread so it doesn't prevent Django from shutting down
        bot_thread = threading.Thread(target=start_bot, daemon=True, name="TelegramBot")
        bot_thread.start()
        logger.info("Telegram bot thread started")