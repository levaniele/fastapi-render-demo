from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = Field(default="local", alias="APP_ENV")
    database_url: str = Field(default="", alias="DATABASE_URL")
    secret_key: str = Field(default="fallback-key-for-dev", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_hours: int = Field(
        default=24, alias="ACCESS_TOKEN_EXPIRE_HOURS"
    )
    reset_token_expire_minutes: int = Field(
        default=30, alias="RESET_TOKEN_EXPIRE_MINUTES"
    )
    allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="ALLOWED_ORIGINS",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    docs_enabled: bool = Field(default=True, alias="DOCS_ENABLED")
    docs_in_production: bool = Field(default=False, alias="DOCS_IN_PRODUCTION")

    def parsed_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        if self.is_production:
            return origins
        defaults = ["http://localhost:3000", "http://127.0.0.1:3000"]
        merged: list[str] = []
        for origin in origins + defaults:
            if origin and origin not in merged:
                merged.append(origin)
        return merged or ["*"]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
