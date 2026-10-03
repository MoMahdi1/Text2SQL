from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(default="", repr=False)
    gemini_model: str = "gemini-2.5-flash"
    database_url: str = (
        "mysql+pymysql://readonly_user:readonly_password@localhost:3306/employee_ai"
    )
    query_row_limit: int = Field(default=100, ge=1, le=1000)
    query_timeout_ms: int = Field(default=5000, ge=500, le=30000)


@lru_cache
def get_settings() -> Settings:
    return Settings()

