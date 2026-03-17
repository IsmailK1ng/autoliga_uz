from django.apps import AppConfig
import threading
import os


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import main.admin
        import main.signals

        if os.environ.get('RUN_MAIN') != 'true':
            return

        def start_bot():
            import asyncio
            import sys
            bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Autoliga_Botfile')
            sys.path.insert(0, bot_dir)
            from bot import main as bot_main

            # Yangi event loop yaratamiz — signal muammosini hal qiladi
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot_main())

        thread = threading.Thread(target=start_bot, daemon=True)
        thread.start()