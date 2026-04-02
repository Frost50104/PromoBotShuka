from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CodeStatus, PromoCode, User


# ── Users ─────────────────────────────────────────────────────────────────────

async def get_user_by_phone(db: AsyncSession, phone: str) -> User | None:
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_or_create_user(
    db: AsyncSession, phone: str, name: str | None, email: str | None
) -> User:
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(phone=phone, name=name, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def user_has_code(db: AsyncSession, user: User) -> PromoCode | None:
    result = await db.execute(
        select(PromoCode).where(PromoCode.assigned_to_user_id == user.id)
    )
    return result.scalar_one_or_none()


async def assign_code(db: AsyncSession, user: User) -> PromoCode | None:
    """Выдать пользователю свободный код (защита от race condition)."""
    result = await db.execute(
        select(PromoCode)
        .where(PromoCode.status == CodeStatus.AVAILABLE)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    code = result.scalar_one_or_none()
    if code is None:
        return None

    code.status = CodeStatus.ASSIGNED
    code.assigned_to_user_id = user.id
    code.assigned_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(code)
    return code


# ── Stats & Export ────────────────────────────────────────────────────────────

async def get_stats(db: AsyncSession) -> dict:
    total = await db.scalar(select(func.count()).select_from(PromoCode))
    assigned = await db.scalar(
        select(func.count()).select_from(PromoCode).where(PromoCode.status == CodeStatus.ASSIGNED)
    )
    users = await db.scalar(select(func.count()).select_from(User))
    return {
        "total": total or 0,
        "assigned": assigned or 0,
        "available": (total or 0) - (assigned or 0),
        "users": users or 0,
    }


async def import_codes(db: AsyncSession, lines: list[str]) -> tuple[int, int]:
    added = skipped = 0
    for line in lines:
        raw = line.strip()
        if not raw:
            continue
        exists = await db.scalar(select(PromoCode).where(PromoCode.raw_code == raw))
        if exists:
            skipped += 1
            continue
        db.add(PromoCode(raw_code=raw))
        added += 1
    if added:
        await db.commit()
    return added, skipped


async def get_all_users_with_codes(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(User, PromoCode)
        .outerjoin(PromoCode, PromoCode.assigned_to_user_id == User.id)
        .order_by(User.created_at.desc())
    )
    rows = []
    for user, code in result.all():
        rows.append({
            "phone": user.phone,
            "name": user.name or "",
            "email": user.email or "",
            "code": code.raw_code if code else "",
            "issued_at": code.assigned_at.strftime("%d.%m.%Y %H:%M") if code and code.assigned_at else "",
            "registered_at": user.created_at.strftime("%d.%m.%Y %H:%M"),
        })
    return rows
