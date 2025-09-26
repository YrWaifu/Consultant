from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEBUG: bool = False
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str
    S3_ENDPOINT: str | None = None
    S3_BUCKET: str | None = None
    BASE_URL: str = "http://localhost:8000"


settings = Settings() # читает .env