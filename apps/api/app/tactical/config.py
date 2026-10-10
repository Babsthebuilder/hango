"""Versioned, inspectable configuration for tactical engine v0.1."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TacticalConfig(BaseModel):
    """All provisional tactical constants; none are learned or calibrated."""

    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    model_version: str = "tactical-v0.1"
    configuration_version: str = "tactical-config-v0.1"

    support_radius_m: float = Field(default=35.0, gt=0.0)
    minimum_support_separation_m: float = Field(default=4.0, gt=0.0)
    minimum_triangle_area_m2: float = Field(default=1.0, ge=0.0)
    minimum_triangle_angle_degrees: float = Field(default=10.0, ge=0.0, lt=60.0)

    lane_corridor_radius_m: float = Field(default=2.0, gt=0.0)
    lane_falloff_m: float = Field(default=3.0, gt=0.0)
    minimum_edge_accessibility: float = Field(default=0.25, ge=0.0, le=1.0)

    pressure_sigma_m: float = Field(default=4.5, gt=0.0)
    default_defender_weight: float = Field(default=1.0, ge=0.0)
    pressure_lane_samples: int = Field(default=9, ge=2, le=101)
    pressure_grid_step_m: float = Field(default=2.0, gt=0.0)

    opportunity_risk_lambda: float = Field(default=0.35, ge=0.0)
    risk_lane_weight: float = Field(default=0.7, ge=0.0)
    risk_pressure_weight: float = Field(default=0.3, ge=0.0)
    pressure_normalization_scale: float = Field(default=2.0, gt=0.0)

    triangle_geometry_weight: float = Field(default=0.15, ge=0.0)
    triangle_direct_lane_weight: float = Field(default=0.30, ge=0.0)
    triangle_third_man_weight: float = Field(default=0.25, ge=0.0)
    triangle_progression_weight: float = Field(default=0.20, ge=0.0)
    triangle_pressure_weight: float = Field(default=0.10, ge=0.0)
    minimum_tactical_triangle_score: float = Field(default=0.35, ge=0.0, le=1.0)
    max_reported_routes: int = Field(default=10, ge=1, le=100)

    interaction_neutral_tolerance: float = Field(default=0.01, ge=0.0)

    @model_validator(mode="after")
    def validate_weights(self) -> "TacticalConfig":
        risk_total = self.risk_lane_weight + self.risk_pressure_weight
        if risk_total <= 0:
            raise ValueError("risk weights must have a positive sum")

        triangle_total = (
            self.triangle_geometry_weight
            + self.triangle_direct_lane_weight
            + self.triangle_third_man_weight
            + self.triangle_progression_weight
            + self.triangle_pressure_weight
        )
        if triangle_total <= 0:
            raise ValueError("triangle score weights must have a positive sum")
        return self


DEFAULT_TACTICAL_CONFIG = TacticalConfig()
