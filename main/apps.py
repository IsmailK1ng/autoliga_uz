from django.apps import AppConfig
import threading
import os


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import main.admin

        if os.environ.get('RUN_MAIN') != 'true':
            return

        def start_bot():
            import asyncio
            import sys
            sys.path.insert(0, 'Autoliga_uz')
            from bot import main as bot_main

            # Yangi event loop yaratamiz — signal muammosini hal qiladi
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot_main())

        thread = threading.Thread(target=start_bot, daemon=True)
        thread.start()