from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Real-Estate"
    env: str = "development"

    async_database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/real_estate_db"
    sync_database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/real_estate_db"

    redis_url: str = "redis://redis:6379/0"

    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    otp_expire_minutes: int = 5
    otp_max_attempts: int = 3
    otp_max_requests_per_hour: int = 5

    permission_cache_ttl_hours: int = 24

    sms_enabled: bool = False
    sms_provider: str = "msg91"
    msg91_auth_key: str | None = None
    msg91_template_id: str | None = None
    msg91_sender_id: str | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_number: str | None = None

    email_enabled: bool = False
    frontend_base_url: str = "http://localhost:3000"
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "no-reply@real-estate.local"
    smtp_use_tls: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
