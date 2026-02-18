"""Application configuration."""

import os
from datetime import datetime
from typing import List

from dotenv import load_dotenv
import pytz

load_dotenv()


class Config:
    """Application configuration class."""

    # Bot settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./promo_bot.db"
    )

    # Admin settings
    ADMIN_IDS: List[int] = [
        int(id_.strip())
        for id_ in os.getenv("ADMIN_IDS", "").split(",")
        if id_.strip()
    ]

    # Promo period settings
    PROMO_START: datetime = datetime.strptime(
        os.getenv("PROMO_START", "2026-03-01"),
        "%Y-%m-%d"
    ).replace(tzinfo=pytz.UTC)

    PROMO_END: datetime = datetime.strptime(
        os.getenv("PROMO_END", "2026-05-30"),
        "%Y-%m-%d"
    ).replace(hour=23, minute=59, second=59, tzinfo=pytz.UTC)

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """Validate configuration."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set")

        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL is not set")

        if cls.PROMO_START >= cls.PROMO_END:
            raise ValueError("PROMO_START must be before PROMO_END")


config = Config()
