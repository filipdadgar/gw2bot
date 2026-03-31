"""Runtime settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration shared across runtime components."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gw2_host_bridge_enabled: bool = Field(default=True, alias="GW2_HOST_BRIDGE_ENABLED")
    gw2_capture_source: str = Field(default="host", alias="GW2_CAPTURE_SOURCE")
    gw2_input_source: str = Field(default="host", alias="GW2_INPUT_SOURCE")
    gw2_data_dir: str = Field(default="data", alias="GW2_DATA_DIR")

    gw2_api_host: str = Field(default="0.0.0.0", alias="GW2_API_HOST")
    gw2_api_port: int = Field(default=8000, alias="GW2_API_PORT")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Provide a singleton settings instance for dependency injection."""

    return Settings()
