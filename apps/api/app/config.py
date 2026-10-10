"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings that do not alter the mathematical specification."""

    model_config = SettingsConfigDict(env_prefix="HANGO_", env_file=".env", extra="ignore")

    env: str = "development"
    model_version: str = "tactical-v0.1"


settings = Settings()
