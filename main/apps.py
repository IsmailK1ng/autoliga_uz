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

        # Only start bot in main process, not in auto-reloader
        if os.environ.get('RUN_MAIN') != 'true':
            return

        def start_bot():
            """Start the Telegram bot in a separate thread with proper error handling"""
            try:
                import asyncio
                import sys

                # Add bot directory to Python path
                bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Autoliga_Botfile')
                sys.path.insert(0, bot_dir)

                # Import bot's main function
                from bot import main as bot_main

                # Create new event loop for the bot to avoid conflicts with Django's async code
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                logger.info("Starting Telegram bot...")
                loop.run_until_complete(bot_main())

            except Exception as e:
                logger.error(f"Telegram bot crashed: {e}", exc_info=True)
                # In production, you might want to restart the bot here
                # For now, we'll let the thread die and log the error

        # Start bot in a daemon thread so it doesn't prevent Django from shutting down
        bot_thread = threading.Thread(target=start_bot, daemon=True, name="TelegramBot")
        bot_thread.start()
        logger.info("Telegram bot thread started")