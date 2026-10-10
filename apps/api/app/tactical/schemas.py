"""Structured calculation objects returned by tactical engine v0.1."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.models import CounterfactualState, Snapshot, Team


class CalculatedModel(BaseModel):
    """Immutable model that rejects NaN and infinity."""

    model_config = ConfigDict(frozen=True, allow_inf_nan=False)


class TriangleRejection(StrEnum):
    SUPPORT_PLAYERS_TOO_CLOSE = "SUPPORT_PLAYERS_TOO_CLOSE"
    AREA_BELOW_MINIMUM = "AREA_BELOW_MINIMUM"
    ANGLE_BELOW_MINIMUM = "ANGLE_BELOW_MINIMUM"
    DEGENERATE_GEOMETRY = "DEGENERATE_GEOMETRY"


class InteractionSign(StrEnum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class SideLengths(CalculatedModel):
    carrier_to_b_m: float = Field(ge=0.0)
    carrier_to_c_m: float = Field(ge=0.0)
    b_to_c_m: float = Field(ge=0.0)


class InteriorAngles(CalculatedModel):
    carrier_degrees: float = Field(ge=0.0, le=180.0)
    b_degrees: float = Field(ge=0.0, le=180.0)
    c_degrees: float = Field(ge=0.0, le=180.0)


class TriangleGeometry(CalculatedModel):
    distances: SideLengths
    angles: InteriorAngles
    area_m2: float = Field(ge=0.0)
    shape_quality: float = Field(ge=0.0, le=1.0)


class TriangleCandidate(CalculatedModel):
    triangle_id: str
    snapshot_id: str
    player_ids: tuple[str, str, str]
    geometry: TriangleGeometry
    geometrically_valid: bool
    rejection_reasons: tuple[TriangleRejection, ...] = ()


class DefenderLaneMeasurement(CalculatedModel):
    defender_id: str
    projection_parameter: float
    segment_distance_m: float = Field(ge=0.0)
    relevant_to_segment: bool
    corridor_intrusion: bool
    accessibility_factor: float = Field(ge=0.0, le=1.0)


class LaneAccessibility(CalculatedModel):
    origin_id: str
    target_id: str
    distance_m: float = Field(gt=0.0)
    accessibility: float = Field(ge=0.0, le=1.0)
    nearest_relevant_defender_id: str | None
    minimum_clearance_m: float | None = Field(default=None, ge=0.0)
    corridor_intruder_ids: tuple[str, ...] = ()
    defender_measurements: tuple[DefenderLaneMeasurement, ...] = ()


class PressureSamples(CalculatedModel):
    at_origin: float = Field(ge=0.0)
    at_target: float = Field(ge=0.0)
    along_lane: tuple[float, ...]
    maximum_along_lane: float = Field(ge=0.0)
    mean_along_lane: float = Field(ge=0.0)


class PressureGrid(CalculatedModel):
    x_coordinates: tuple[float, ...]
    y_coordinates: tuple[float, ...]
    values: tuple[tuple[float, ...], ...]


class PassingEdge(CalculatedModel):
    origin_id: str
    target_id: str
    distance_m: float = Field(gt=0.0)
    lane_accessibility: float = Field(ge=0.0, le=1.0)
    progression_value: float = Field(ge=-1.0, le=1.0)
    pressure_at_target: float = Field(ge=0.0)


class PassingGraph(CalculatedModel):
    snapshot_id: str
    attacking_team: Team
    node_ids: tuple[str, ...]
    edges: tuple[PassingEdge, ...]


class OpportunityComponents(CalculatedModel):
    lane_accessibility: float = Field(ge=0.0, le=1.0)
    progression_value: float = Field(ge=-1.0, le=1.0)
    turnover_risk: float = Field(ge=0.0, le=1.0)
    risk_penalty: float = Field(ge=0.0)


class RouteOpportunity(CalculatedModel):
    route_id: str
    player_ids: tuple[str, ...]
    components: OpportunityComponents
    score: float


class TriangleScoreComponents(CalculatedModel):
    geometry: float = Field(ge=0.0, le=1.0)
    direct_lane: float = Field(ge=0.0, le=1.0)
    third_man: float = Field(ge=0.0, le=1.0)
    progression: float = Field(ge=0.0, le=1.0)
    receiver_pressure: float = Field(ge=0.0, le=1.0)


class TacticalTriangleAnalysis(CalculatedModel):
    triangle: TriangleCandidate
    direct_lanes: tuple[LaneAccessibility, LaneAccessibility]
    routes: tuple[RouteOpportunity, ...]
    score_components: TriangleScoreComponents
    heuristic_score: float = Field(ge=0.0, le=1.0)
    tactically_useful: bool
    model_version: str
    configuration_version: str


class InteractionResult(CalculatedModel):
    label: str = "modeled relational interaction"
    u_00: float
    u_10: float
    u_01: float
    u_11: float
    interaction_value: float
    sign: InteractionSign
    model_version: str
    configuration_version: str


class PressureSummary(CalculatedModel):
    at_ball_carrier: float = Field(ge=0.0)
    mean_attacking_player_pressure: float = Field(ge=0.0)
    maximum_attacking_player_pressure: float = Field(ge=0.0)


class SnapshotAnalysis(CalculatedModel):
    snapshot_id: str
    ball_carrier_id: str
    attacking_team: Team
    detected_triangles: tuple[TriangleCandidate, ...]
    ranked_tactical_triangles: tuple[TacticalTriangleAnalysis, ...]
    best_passing_routes: tuple[RouteOpportunity, ...]
    pressure_summary: PressureSummary
    opportunity_score: float
    interaction: InteractionResult | None = None
    model_version: str
    configuration_version: str


class CounterfactualComparison(CalculatedModel):
    baseline: SnapshotAnalysis
    alternative: SnapshotAnalysis
    opportunity_delta: float


class PressureGridResult(CalculatedModel):
    grid: PressureGrid
    evidence_classification: str = "MODEL_ESTIMATE"
    model_version: str
    configuration_version: str


class PressureGridComparison(CalculatedModel):
    baseline: PressureGridResult
    alternative: PressureGridResult | None = None


class AnalyzeRequest(CalculatedModel):
    snapshot: Snapshot
    ball_carrier_id: str
    attacking_team: Team


class InteractionRequest(CalculatedModel):
    snapshot: Snapshot
    counterfactual: CounterfactualState
    ball_carrier_id: str
    support_b_id: str
    support_c_id: str
    attacking_team: Team


class CompareRequest(CalculatedModel):
    snapshot: Snapshot
    counterfactual: CounterfactualState
    ball_carrier_id: str
    attacking_team: Team


class PressureGridRequest(CalculatedModel):
    snapshot: Snapshot
    attacking_team: Team
    counterfactual: CounterfactualState | None = None
