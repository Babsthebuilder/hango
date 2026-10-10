"""Versioned configuration for deterministic evidence verification."""

from pydantic import BaseModel, ConfigDict, Field


class EvidenceConfig(BaseModel):
    """Canonicalization and numeric-comparison policy."""

    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    schema_version: str = "evidence-schema-v0.1"
    configuration_version: str = "evidence-config-v0.1"
    float_decimal_places: int = Field(default=9, ge=6, le=15)
    absolute_tolerance: float = Field(default=1e-9, ge=0.0)
    relative_tolerance: float = Field(default=1e-9, ge=0.0)
    calculation_id_hash_length: int = Field(default=20, ge=16, le=64)
    compatible_snapshot_schema_versions: tuple[str, ...] = ("0.1",)


DEFAULT_EVIDENCE_CONFIG = EvidenceConfig()
