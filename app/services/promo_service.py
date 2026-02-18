"""Promo code service for managing promo codes."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PromoCode, CodeStatus, User
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PromoService:
    """Service for promo code operations."""

    @staticmethod
    async def get_available_code(
        session: AsyncSession,
        user: User,
    ) -> Optional[PromoCode]:
        """
        Get an available promo code and assign it to the user.

        Uses SELECT ... FOR UPDATE SKIP LOCKED to prevent race conditions.

        Args:
            session: Database session
            user: User to assign the code to

        Returns:
            PromoCode instance or None if no codes available
        """
        # First check if user already has a code
        existing_code_result = await session.execute(
            select(PromoCode).where(
                PromoCode.assigned_to_user_id == user.id
            )
        )
        existing_code = existing_code_result.scalar_one_or_none()

        if existing_code:
            logger.warning(
                "User already has a promo code",
                user_id=user.id,
                telegram_id=user.telegram_id,
                code_id=existing_code.id,
            )
            return None

        # Find and lock an available code
        result = await session.execute(
            select(PromoCode)
            .where(PromoCode.status == CodeStatus.AVAILABLE)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        code = result.scalar_one_or_none()

        if not code:
            logger.error(
                "No promo codes available",
                user_id=user.id,
                telegram_id=user.telegram_id,
            )
            return None

        # Assign code to user
        code.status = CodeStatus.ASSIGNED
        code.assigned_to_user_id = user.id
        code.assigned_at = datetime.utcnow()

        await session.commit()
        await session.refresh(code)

        logger.info(
            "Promo code assigned to user",
            user_id=user.id,
            telegram_id=user.telegram_id,
            code_id=code.id,
            raw_code=code.raw_code,
        )

        return code

    @staticmethod
    async def user_has_code(
        session: AsyncSession,
        user: User,
    ) -> bool:
        """
        Check if user already has an assigned code.

        Args:
            session: Database session
            user: User to check

        Returns:
            True if user has a code, False otherwise
        """
        result = await session.execute(
            select(func.count(PromoCode.id)).where(
                PromoCode.assigned_to_user_id == user.id
            )
        )
        count = result.scalar_one()
        return count > 0

    @staticmethod
    async def add_codes(
        session: AsyncSession,
        codes: list[str],
    ) -> tuple[int, int]:
        """
        Add multiple promo codes to the database.

        Args:
            session: Database session
            codes: List of raw code strings

        Returns:
            Tuple of (added_count, skipped_count)
        """
        added = 0
        skipped = 0

        for raw_code in codes:
            raw_code = raw_code.strip()
            if not raw_code:
                continue

            # Check if code already exists
            result = await session.execute(
                select(PromoCode).where(PromoCode.raw_code == raw_code)
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.debug("Code already exists, skipping", raw_code=raw_code)
                skipped += 1
                continue

            # Add new code
            code = PromoCode(raw_code=raw_code)
            session.add(code)
            added += 1

        await session.commit()

        logger.info(
            "Codes import completed",
            added=added,
            skipped=skipped,
            total=len(codes),
        )

        return added, skipped

    @staticmethod
    async def get_codes_stats(
        session: AsyncSession,
    ) -> dict[str, int]:
        """
        Get statistics about promo codes.

        Returns:
            Dictionary with available, assigned, and total counts
        """
        total_result = await session.execute(
            select(func.count(PromoCode.id))
        )
        total = total_result.scalar_one()

        available_result = await session.execute(
            select(func.count(PromoCode.id)).where(
                PromoCode.status == CodeStatus.AVAILABLE
            )
        )
        available = available_result.scalar_one()

        assigned_result = await session.execute(
            select(func.count(PromoCode.id)).where(
                PromoCode.status == CodeStatus.ASSIGNED
            )
        )
        assigned = assigned_result.scalar_one()

        return {
            "total": total,
            "available": available,
            "assigned": assigned,
        }
