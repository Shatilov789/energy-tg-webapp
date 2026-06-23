"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/energy_crm"
    database_url_sync: str = "postgresql://postgres:postgres@db:5432/energy_crm"

    redis_url: str = "redis://redis:6379/0"

    telegram_bot_token: str = ""
    admin_telegram_id: int = 0

    # Reminder: days before sending notification about unfilled step
    reminder_delay_days: int = 2

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
