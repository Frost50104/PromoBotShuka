"""Database models."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    Enum,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class CodeStatus(enum.Enum):
    """Promo code status enum."""
    AVAILABLE = "available"
    ASSIGNED = "assigned"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationship
    promo_codes: Mapped[list["PromoCode"]] = relationship(
        back_populates="assigned_user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, telegram_id={self.telegram_id}, "
            f"username={self.username})>"
        )


class PromoCode(Base):
    """Promo code model."""

    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_code: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    status: Mapped[CodeStatus] = mapped_column(
        Enum(CodeStatus, name="code_status"),
        default=CodeStatus.AVAILABLE,
        nullable=False,
        index=True
    )
    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    assigned_user: Mapped[Optional["User"]] = relationship(
        back_populates="promo_codes"
    )

    __table_args__ = (
        Index("ix_promo_codes_status_assigned", "status", "assigned_to_user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<PromoCode(id={self.id}, raw_code={self.raw_code}, "
            f"status={self.status.value})>"
        )


class Admin(Base):
    """Admin model."""

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Admin(id={self.id}, telegram_id={self.telegram_id}, "
            f"username={self.username})>"
        )
