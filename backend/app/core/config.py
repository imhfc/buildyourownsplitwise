from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "BYOSW"
    APP_SUBTITLE: str = "絕對免費，全部AI開發的分帳系統"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://splitewise:splitewise@localhost:5432/splitewise"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-a-real-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Exchange rate
    EXCHANGE_RATE_API_URL: str = "https://tw.rter.info/capi.php"
    EXCHANGE_RATE_CACHE_TTL: int = 1800  # 30 minutes

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
