from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "SpliteWise"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://splitewise:splitewise@localhost:5432/splitewise"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-a-real-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Exchange rate
    EXCHANGE_RATE_API_URL: str = "https://tw.rter.info/capi.php"
    EXCHANGE_RATE_CACHE_TTL: int = 1800  # 30 minutes

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
