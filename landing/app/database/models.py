import enum
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime, Enum, ForeignKey,
    Integer, String, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class CodeStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    promo_codes: Mapped[list["PromoCode"]] = relationship(back_populates="assigned_user")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_code: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[CodeStatus] = mapped_column(
        Enum(CodeStatus), default=CodeStatus.AVAILABLE, nullable=False, index=True
    )
    assigned_to_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    assigned_user: Mapped["User | None"] = relationship(back_populates="promo_codes")

    __table_args__ = (
        Index("ix_promo_codes_status_user", "status", "assigned_to_user_id"),
    )
