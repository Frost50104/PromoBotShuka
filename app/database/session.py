"""Database session management."""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)

from app.config import config
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Create async engine
# Pool parameters only for PostgreSQL (not supported by SQLite)
engine_kwargs = {
    "echo": False,
}

if "postgresql" in config.DATABASE_URL:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    })

engine: AsyncEngine = create_async_engine(
    config.DATABASE_URL,
    **engine_kwargs,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database (create tables)."""
    from .base import Base

    logger.info("Initializing database", url=config.DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close database connection."""
    logger.info("Closing database connection")
    await engine.dispose()
