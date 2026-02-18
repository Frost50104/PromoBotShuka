"""User service for managing users."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.utils.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user operations."""

    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one.

        Args:
            session: Database session
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name

        Returns:
            Tuple of (User instance, is_created flag)
        """
        # Try to get existing user
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Update last_seen_at and user info
            user.last_seen_at = datetime.utcnow()
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            await session.commit()

            logger.info(
                "Existing user accessed bot",
                telegram_id=telegram_id,
                username=username,
            )
            return user, False

        # Create new user
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        logger.info(
            "New user created",
            telegram_id=telegram_id,
            username=username,
            user_id=user.id,
        )
        return user, True

    @staticmethod
    async def get_user_by_telegram_id(
        session: AsyncSession,
        telegram_id: int,
    ) -> Optional[User]:
        """Get user by Telegram ID."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_users(
        session: AsyncSession,
    ) -> list[User]:
        """
        Get all users ordered by creation date.

        Args:
            session: Database session

        Returns:
            List of User instances
        """
        result = await session.execute(
            select(User).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())
