"""Feature flag configuration for optional enhancements."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FeatureFlags(BaseSettings):
    """Optional enhancement feature toggles."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gw2_minimap_detection_enabled: bool = Field(default=False, alias="GW2_MINIMAP_DETECTION_ENABLED")
    gw2_dynamic_prioritization_enabled: bool = Field(default=False, alias="GW2_DYNAMIC_PRIORITIZATION_ENABLED")
    gw2_prioritization_distance_weight: float = Field(default=0.5, alias="GW2_PRIORITIZATION_DISTANCE_WEIGHT")
    gw2_prioritization_confidence_weight: float = Field(default=0.3, alias="GW2_PRIORITIZATION_CONFIDENCE_WEIGHT")
    gw2_prioritization_rarity_weight: float = Field(default=0.2, alias="GW2_PRIORITIZATION_RARITY_WEIGHT")


@lru_cache(maxsize=1)
def get_feature_flags() -> FeatureFlags:
    """Provide a singleton feature flags instance for dependency injection."""
    return FeatureFlags()
