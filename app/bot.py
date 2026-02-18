"""Bot initialization."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import config
from app.handlers import setup_routers
from app.middleware import DbSessionMiddleware
from app.utils.logging import get_logger

logger = get_logger(__name__)


def create_bot() -> Bot:
    """Create and configure bot instance."""
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    logger.info("Bot instance created")
    return bot


def create_dispatcher() -> Dispatcher:
    """Create and configure dispatcher."""
    dp = Dispatcher()

    # Setup middleware
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    logger.info("Middleware configured")

    # Setup routers
    main_router = setup_routers()
    dp.include_router(main_router)
    logger.info("Routers configured")

    return dp
