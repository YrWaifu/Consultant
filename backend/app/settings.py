from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


# Определяем путь к .env файлу (в корне проекта)
# В docker рабочая директория /app, в локальной разработке - корень проекта
BASE_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Игнорировать дополнительные поля из .env, которые не определены в классе
    )
    DEBUG: bool = False
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str
    S3_ENDPOINT: str | None = None
    S3_BUCKET: str | None = None
    BASE_URL: str = "http://localhost:8000"
    
    # Google reCAPTCHA v2
    RECAPTCHA_SITE_KEY: str = ""
    RECAPTCHA_SECRET_KEY: str = ""
    
    # Контактная информация для футера (читается из .env)
    SITE_NAME: str = "РекВизор"
    CONTACT_EMAIL: str | None = None
    CONTACT_ADDRESS: str | None = None


settings = Settings() # читает .env