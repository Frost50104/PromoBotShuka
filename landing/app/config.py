from pydantic_settings import BaseSettings
from datetime import date
import secrets


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./vesnaidet.db"
    SECRET_KEY: str = secrets.token_hex(32)
    ADMIN_LOGIN: str = "admin"
    ADMIN_PASSWORD: str = "Uppetit01@"

    SMSC_LOGIN: str = ""
    SMSC_PASSWORD: str = ""
    SMSC_SENDER: str = "UPPETIT"

    PROMO_START: date = date(2026, 4, 1)
    PROMO_END: date = date(2026, 5, 30)

    OTP_EXPIRE_SECONDS: int = 300  # 5 минут
    OTP_MAX_ATTEMPTS: int = 3

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
