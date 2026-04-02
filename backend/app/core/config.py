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

    # Exchange rate
    EXCHANGE_RATE_API_URL: str = "https://tw.rter.info/capi.php"

    # Google OAuth (comma-separated list of accepted client IDs: web,ios,android)
    GOOGLE_CLIENT_IDS: str = ""

    # Rate limiter — 測試環境（pytest）自動停用，避免測試互相干擾
    TESTING: bool = False

    # CORS — 逗號分隔，生產環境應設為實際網域，例如 https://app.example.com
    ALLOWED_ORIGINS: str = "*"

    # SendGrid
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@byosw.duckdns.org"

    # Frontend URL (for email invitation links)
    FRONTEND_URL: str = "https://byosw.duckdns.org"

    # Email invitation
    EMAIL_INVITATION_EXPIRE_DAYS: int = 7

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
