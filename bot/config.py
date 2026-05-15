from datetime import date, datetime
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str   # postgresql://user:pass@host:5432/db
    OWNER_ID: int       # Your Telegram numeric user ID
    REMINDER_HOUR: int = 23
    REMINDER_MINUTE: int = 0
    TIMEZONE: str = "Europe/Warsaw"

    class Config:
        env_file = ".env"


settings = Settings()


def today_tz() -> date:
    """Current date in the configured local timezone (avoids UTC drift after midnight)."""
    return datetime.now(ZoneInfo(settings.TIMEZONE)).date()
