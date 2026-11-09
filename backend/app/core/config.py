"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Fails safe: the dev auth bypass stays off unless development is requested explicitly.
    app_env: str = "production"
    app_secret_key: str = "change-me-in-production"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/energy_crm"
    database_url_sync: str = "postgresql://postgres:postgres@db:5432/energy_crm"

    redis_url: str = "redis://redis:6379/0"

    telegram_bot_token: str = ""
    admin_telegram_id: int = 0
    # How long a Telegram Web App launch stays valid, measured from its auth_date.
    telegram_auth_max_age_seconds: int = 86400
    webapp_url: str = ""  # Telegram Web App URL for the button in push notifications

    # Comma-separated origins allowed to call the API from another site.
    # Stays empty when the web app and the API share one origin.
    cors_origins: str = ""

    # Reminder: days before sending notification about unfilled step
    reminder_delay_days: int = 2

    # extra="ignore": the shared .env also carries variables meant for other containers (POSTGRES_*).
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.is_development:
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
