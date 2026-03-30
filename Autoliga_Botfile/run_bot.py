"""
Standalone entry-point for the Telegram bot.

Usage:
    python Autoliga_Botfile/run_bot.py          # run directly
    docker compose up bot                       # via docker-compose

The bot module (bot.py) handles Django setup internally,
so this file is just a thin runner with signal handling.
"""
import asyncio
import logging
import os
import signal
import sys

# ── Make project root importable ────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
for path in (PROJECT_ROOT, BOT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

# ── Basic logging (bot.py sets up full logging after Django init) ────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_bot")


async def _run():
    from bot import main as bot_main  # noqa: PLC0415 — imported after sys.path setup

    await bot_main()


def _handle_sigterm(signum, frame):
    logger.info("SIGTERM received — shutting down bot.")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_sigterm)
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C).")
    except SystemExit:
        pass
    except Exception as exc:
        logger.critical("Bot crashed: %s", exc, exc_info=True)
        sys.exit(1)