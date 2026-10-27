import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "LMS API"
    app_env: Environment = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://lms:lms_dev_password@localhost:5432/lms"

    jwt_secret_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0, le=1440)

    cors_origins: list[str] = []

    @model_validator(mode="after")
    def validate_security(self):
        secret = self.jwt_secret_key.get_secret_value()

        if self.app_env == "production":
            if len(secret) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must contain at least 32 characters in production."
                )
            if "development-only" in secret.lower():
                raise ValueError("Development JWT secret is forbidden in production.")
            if self.debug:
                raise ValueError("DEBUG must be false in production.")
            if "localhost" in self.database_url:
                raise ValueError("Production DATABASE_URL must not use localhost.")
        elif not secret:
            self.jwt_secret_key = SecretStr("development-only-secret-change-me")

        return self


@lru_cache
def get_settings() -> Settings:
    env = os.getenv("APP_ENV", "development").lower()
    if env not in {"development", "test", "production"}:
        raise ValueError(f"Unsupported APP_ENV: {env}")

    env_file = PROJECT_ROOT / f".env.{env}"
    return Settings(_env_file=env_file if env_file.exists() else None)


settings = get_settings()
