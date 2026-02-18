"""Admin service for managing administrators."""

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Admin
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AdminService:
    """Service for admin operations."""

    @staticmethod
    async def is_admin(
        session: AsyncSession,
        telegram_id: int,
    ) -> bool:
        """
        Check if user is admin.

        Args:
            session: Database session
            telegram_id: Telegram user ID

        Returns:
            True if user is admin, False otherwise
        """
        result = await session.execute(
            select(func.count(Admin.id)).where(
                Admin.telegram_id == telegram_id
            )
        )
        count = result.scalar_one()
        return count > 0

    @staticmethod
    async def add_admin(
        session: AsyncSession,
        telegram_id: int,
        first_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Add a new admin.

        Args:
            session: Database session
            telegram_id: Telegram user ID
            first_name: Admin's first name
            username: Admin's username

        Returns:
            Tuple of (success, message)
        """
        # Check if admin already exists
        result = await session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            logger.warning(
                "Admin already exists",
                telegram_id=telegram_id,
            )
            return False, "Этот пользователь уже является админом"

        # Create new admin
        admin = Admin(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        logger.info(
            "New admin added",
            telegram_id=telegram_id,
            username=username,
            admin_id=admin.id,
        )
        return True, "Админ успешно добавлен"

    @staticmethod
    async def delete_admin(
        session: AsyncSession,
        telegram_id: int,
    ) -> tuple[bool, str]:
        """
        Delete an admin.

        Args:
            session: Database session
            telegram_id: Telegram user ID

        Returns:
            Tuple of (success, message)
        """
        result = await session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            logger.warning(
                "Admin not found for deletion",
                telegram_id=telegram_id,
            )
            return False, "Админ не найден"

        await session.delete(admin)
        await session.commit()

        logger.info(
            "Admin deleted",
            telegram_id=telegram_id,
            admin_id=admin.id,
        )
        return True, "Админ успешно удален"

    @staticmethod
    async def get_all_admins(
        session: AsyncSession,
    ) -> list[Admin]:
        """
        Get all admins.

        Args:
            session: Database session

        Returns:
            List of Admin instances
        """
        result = await session.execute(
            select(Admin).order_by(Admin.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_unique_users_count(
        session: AsyncSession,
    ) -> int:
        """
        Get count of unique users who used the bot.

        Args:
            session: Database session

        Returns:
            Count of unique users
        """
        from app.database.models import User

        result = await session.execute(
            select(func.count(User.id))
        )
        return result.scalar_one()
