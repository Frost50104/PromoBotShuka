"""Main entry point for the bot."""

import asyncio
import signal
import sys

from app.bot import create_bot, create_dispatcher
from app.config import config
from app.database import init_db, close_db
from app.utils.logging import setup_logging, get_logger

# Setup logging
setup_logging(config.LOG_LEVEL)
logger = get_logger(__name__)


async def on_startup() -> None:
    """Execute on bot startup."""
    logger.info("Starting UPPETIT Promo Bot")

    # Validate configuration
    try:
        config.validate()
        logger.info("Configuration validated")
    except ValueError as e:
        logger.error("Configuration error", error=str(e))
        sys.exit(1)

    # Initialize database
    try:
        await init_db()
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        sys.exit(1)

    logger.info("Bot started successfully")


async def on_shutdown() -> None:
    """Execute on bot shutdown."""
    logger.info("Shutting down bot")
    await close_db()
    logger.info("Bot stopped")


async def main() -> None:
    """Main function."""
    # Create bot and dispatcher
    bot = create_bot()
    dp = create_dispatcher()

    # Register startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Handle shutdown signals
    loop = asyncio.get_event_loop()

    def signal_handler(sig):
        logger.info("Received signal, shutting down", signal=sig)
        loop.create_task(dp.stop_polling())

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: signal_handler(s))

    try:
        # Start polling
        logger.info("Starting polling")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error("Error during polling", error=str(e))
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        sys.exit(1)
