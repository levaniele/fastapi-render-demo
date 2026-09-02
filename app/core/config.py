from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = Field(default="local", alias="APP_ENV")
    database_url: str = Field(default="", alias="DATABASE_URL")
    direct_database_url: str = Field(default="", alias="DIRECT_DATABASE_URL")
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
    
    # Observability settings
    observability_enabled: bool = Field(default=True, alias="OBSERVABILITY_ENABLED")
    observability_url: str = Field(
        default="http://localhost:8080",
        alias="OBSERVABILITY_URL"
    )
    obs_api_key: str = Field(default="", alias="OBS_API_KEY")
    version: str = Field(default="1.0.0", alias="VERSION")
    db_log_queries: bool = Field(default=True, alias="DB_LOG_QUERIES")
    db_slow_query_ms: int = Field(default=300, alias="DB_SLOW_QUERY_MS")

    # Cache settings
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")
    cache_live_data_ttl: int = Field(default=60, alias="CACHE_LIVE_DATA_TTL")
    cache_tournament_data_ttl: int = Field(default=300, alias="CACHE_TOURNAMENT_DATA_TTL")
    cache_static_data_ttl: int = Field(default=3600, alias="CACHE_STATIC_DATA_TTL")
    cache_reference_data_ttl: int = Field(default=21600, alias="CACHE_REFERENCE_DATA_TTL")

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
        is_prod = self.app_env.lower() == "production"
        if is_prod:
            self._validate_production_config()
        return is_prod
    
    def _validate_production_config(self) -> None:
        """Validate critical configuration for production environment."""
        errors = []
        
        # Check SECRET_KEY
        if self.secret_key == "fallback-key-for-dev":
            errors.append("SECRET_KEY must be set to a strong value in production")
        elif len(self.secret_key) < 32:
            errors.append(f"SECRET_KEY must be at least 32 characters (current: {len(self.secret_key)})")
        
        # Check DATABASE_URL
        if not self.database_url:
            errors.append("DATABASE_URL must be set in production")
        elif "localhost" in self.database_url or "127.0.0.1" in self.database_url:
            errors.append("DATABASE_URL must not point to localhost in production")
        
        # Check API docs
        if self.docs_enabled and not self.docs_in_production:
            errors.append("API docs should be disabled in production (set DOCS_ENABLED=false)")
        
        if errors:
            error_msg = "Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)


@lru_cache
def get_settings() -> Settings:
    return Settings()
