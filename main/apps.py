from django.apps import AppConfig
import threading
import os


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import main.admin
        import main.signals

        # Faqat local runserver da ishga tushsin
        if os.environ.get('RUN_MAIN') != 'true':
            return

        def start_bot():
            import sys

            # run_bot.py ga to'g'ri yo'l
            bot_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'Autoliga_Botfile'
            )
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            for path in (project_root, bot_dir):
                if path not in sys.path:
                    sys.path.insert(0, path)

            # run_bot.py ichidagi _run() ni ishlatamiz
            import asyncio
            from run_bot import _run  # ← run_bot.py dan import

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_run())
            except Exception as exc:
                import logging
                logging.getLogger("apps").critical("Bot crashed: %s", exc, exc_info=True)
            finally:
                loop.close()

        thread = threading.Thread(target=start_bot, daemon=True, name="TelegramBot")
        thread.start()