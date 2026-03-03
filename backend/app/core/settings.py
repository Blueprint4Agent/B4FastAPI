import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    # Agent customization note:
    # Add project-wide toggles here first. Keep env names stable for scripts.
    ROOT_DIR: Path = Path(__file__).resolve().parents[2]

    APP_NAME: str = os.getenv("APP_NAME", "Blueprint4FastAPI API")
    APP_ENV: str = os.getenv("APP_ENV", "local")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:5173")
    SWAGGER_ENABLED: bool = os.getenv("SWAGGER_ENABLED", "true").lower() == "true"
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES", "60")
    )
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30")
    )
    LOGIN_FAILED_LIMIT: int = int(os.getenv("LOGIN_FAILED_LIMIT", "5"))
    LOGIN_LOCKED_MINUTES: int = int(os.getenv("LOGIN_LOCKED_MINUTES", "5"))

    DB_DRIVER: str = os.getenv("DB_DRIVER", "sqlite+aiosqlite")
    DB_NAME: str = os.getenv("DB_NAME", "template.db")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DATABASE_URL: str | None = None

    REDIS_IN_MEMORY: bool = os.getenv("REDIS_IN_MEMORY", "false").lower() == "true"
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD")
    REDIS_URL: str | None = None

    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "no-reply@example.com")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", os.getenv("SMTP_USER", ""))
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_STARTTLS: bool = os.getenv("SMTP_USE_STARTTLS", "true").lower() == "true"
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    SMTP_TIMEOUT_SECONDS: int = int(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))
    SMTP_VALIDATE_ON_STARTUP: bool = os.getenv("SMTP_VALIDATE_ON_STARTUP", "true").lower() == "true"
    EMAIL_BRAND_NAME: str = os.getenv("EMAIL_BRAND_NAME", "Blueprint4FastAPI")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.DB_DRIVER.startswith("sqlite"):
            db_file = self.ROOT_DIR / self.DB_NAME
            object.__setattr__(self, "DATABASE_URL", f"{self.DB_DRIVER}:///{db_file.as_posix()}")
        else:
            object.__setattr__(
                self,
                "DATABASE_URL",
                (
                    f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}"
                    f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
                ),
            )

        if self.REDIS_PASSWORD:
            redis_url = (
                f"redis://:{self.REDIS_PASSWORD}"
                f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            )
        else:
            redis_url = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        object.__setattr__(self, "REDIS_URL", redis_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def get_smtp_validation_errors(self) -> list[str]:
        if not self.EMAIL_ENABLED:
            return []

        errors: list[str] = []
        if not self.SMTP_HOST.strip():
            errors.append("SMTP_HOST is required when EMAIL_ENABLED=true.")
        if self.SMTP_PORT <= 0:
            errors.append("SMTP_PORT must be greater than 0.")
        if not self.EMAIL_FROM.strip():
            errors.append("EMAIL_FROM is required when EMAIL_ENABLED=true.")
        if self.SMTP_USE_SSL and self.SMTP_USE_STARTTLS:
            errors.append("SMTP_USE_SSL and SMTP_USE_STARTTLS cannot both be true.")

        has_username = bool(self.SMTP_USERNAME.strip())
        has_password = bool(self.SMTP_PASSWORD.strip())
        if has_username != has_password:
            errors.append("SMTP_USERNAME and SMTP_PASSWORD must be set together.")

        return errors


SETTINGS = Settings()
