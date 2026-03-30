import logging
import os
import sys
import threading
import time

from django.apps import AppConfig

logger = logging.getLogger(__name__)

# Maximum restart attempts before giving up
_BOT_MAX_RETRIES = int(os.environ.get("BOT_MAX_RETRIES", "5"))


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        import main.admin  # noqa: F401
        import main.signals  # noqa: F401

        is_runserver = "runserver" in sys.argv
        is_noreload = "--noreload" in sys.argv
        run_main = os.environ.get("RUN_MAIN")

        # Skip in auto-reloader parent process (Django sets RUN_MAIN='true' in worker).
        # With --noreload, RUN_MAIN is never set, so we must still start the bot.
        if is_runserver and not is_noreload and run_main != "true":
            return

        # Skip for management commands (migrate, shell, collectstatic, etc.)
        if not is_runserver:
            return

        def start_bot():
            """Start the bot with exponential-backoff restart on crash."""
            import asyncio

            bot_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "Autoliga_Botfile",
            )
            if bot_dir not in sys.path:
                sys.path.insert(0, bot_dir)

            # bot.py guards against double django.setup(), so this is safe.
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

            from bot import main as bot_main  # noqa: PLC0415

            retry_delay = 5
            for attempt in range(1, _BOT_MAX_RETRIES + 1):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    logger.info("Telegram bot starting (attempt %d/%d)Р В Р вЂ Р В РІР‚С™Р вЂ™Р’В¦", attempt, _BOT_MAX_RETRIES)
                    loop.run_until_complete(bot_main())
                    logger.info("Telegram bot exited cleanly.")
                    break  # clean shutdown Р В Р вЂ Р В РІР‚С™Р Р†Р вЂљРЎСљ don't restart
                except Exception as exc:
                    logger.error(
                        "Telegram bot crashed (attempt %d/%d): %s",
                        attempt, _BOT_MAX_RETRIES, exc,
                        exc_info=True,
                    )
                    if attempt < _BOT_MAX_RETRIES:
                        logger.info("Restarting bot in %dsР В Р вЂ Р В РІР‚С™Р вЂ™Р’В¦", retry_delay)
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 60)  # cap at 60 s
                finally:
                    try:
                        loop.close()
                    except Exception:
                        pass
            else:
                logger.critical(
                    "Telegram bot failed after %d attempts Р В Р вЂ Р В РІР‚С™Р Р†Р вЂљРЎСљ giving up.", _BOT_MAX_RETRIES
                )

        bot_thread = threading.Thread(target=start_bot, daemon=True, name="TelegramBot")
        bot_thread.start()
        logger.info("Telegram bot thread started.")