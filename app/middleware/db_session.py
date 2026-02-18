"""Database session middleware for aiogram."""

from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import async_session_maker
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    """Middleware to provide database session to handlers."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Create session and pass it to handler."""
        async with async_session_maker() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            except Exception as e:
                logger.error(
                    "Error in handler",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                await session.rollback()
                raise
