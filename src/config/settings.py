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

    gw2_training_auto_retrain_enabled: bool = Field(default=False, alias="GW2_TRAINING_AUTO_RETRAIN_ENABLED")
    gw2_training_retrain_interval_seconds: int = Field(default=1800, alias="GW2_TRAINING_RETRAIN_INTERVAL_SECONDS")
    gw2_runtime_policy_enabled: bool = Field(default=False, alias="GW2_RUNTIME_POLICY_ENABLED")
    gw2_runtime_input_enabled: bool = Field(default=False, alias="GW2_RUNTIME_INPUT_ENABLED")
    gw2_runtime_policy_min_confidence: float = Field(default=0.7, alias="GW2_RUNTIME_POLICY_MIN_CONFIDENCE")
    gw2_runtime_signal_interval_ms: int = Field(default=1000, alias="GW2_RUNTIME_SIGNAL_INTERVAL_MS")
    gw2_demo_auto_capture_enabled: bool = Field(default=False, alias="GW2_DEMO_AUTO_CAPTURE_ENABLED")
    gw2_autostart_run_enabled: bool = Field(default=False, alias="GW2_AUTOSTART_RUN_ENABLED")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Provide a singleton settings instance for dependency injection."""

    return Settings()
