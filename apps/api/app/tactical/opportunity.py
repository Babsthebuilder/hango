"""Inspectable provisional route opportunity heuristic."""

from __future__ import annotations

from hashlib import sha256
from statistics import fmean

from app.models import AttackingDirection, Position
from app.tactical.config import DEFAULT_TACTICAL_CONFIG, TacticalConfig
from app.tactical.schemas import (
    LaneAccessibility,
    OpportunityComponents,
    PassingEdge,
    RouteOpportunity,
    TacticalTriangleAnalysis,
    TriangleCandidate,
    TriangleScoreComponents,
)


def attacking_value(position: Position, direction: AttackingDirection) -> float:
    """Return the v0.1 linear pitch-value placeholder in [0, 1]."""

    if direction == AttackingDirection.POSITIVE_X:
        return position.x / 105.0
    return (105.0 - position.x) / 105.0


def progression_value(
    origin: Position,
    target: Position,
    direction: AttackingDirection,
) -> float:
    """Return signed change on the documented linear pitch-value surface."""

    return attacking_value(target, direction) - attacking_value(origin, direction)


def normalized_pressure(pressure: float, config: TacticalConfig) -> float:
    """Map non-negative unbounded pressure to [0, 1) for the risk heuristic."""

    if pressure < 0:
        raise ValueError("pressure must be non-negative")
    return pressure / (pressure + config.pressure_normalization_scale)


def evaluate_route(
    player_ids: tuple[str, ...],
    edges: tuple[PassingEdge, ...],
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
) -> RouteOpportunity:
    """Evaluate Q = L * DeltaV - lambda * R for one directed route."""

    if len(player_ids) < 2 or len(edges) != len(player_ids) - 1:
        raise ValueError("route edges must connect every adjacent player pair")
    for index, edge in enumerate(edges):
        if (edge.origin_id, edge.target_id) != (player_ids[index], player_ids[index + 1]):
            raise ValueError("route edges do not match player order")

    accessibility = 1.0
    for edge in edges:
        accessibility *= edge.lane_accessibility
    progression = sum(edge.progression_value for edge in edges)
    pressure_risk = fmean(
        normalized_pressure(edge.pressure_at_target, config) for edge in edges
    )
    risk_weight_total = config.risk_lane_weight + config.risk_pressure_weight
    turnover_risk = (
        config.risk_lane_weight * (1.0 - accessibility)
        + config.risk_pressure_weight * pressure_risk
    ) / risk_weight_total
    risk_penalty = config.opportunity_risk_lambda * turnover_risk
    score = accessibility * progression - risk_penalty
    route_key = "|".join((*player_ids, config.model_version, config.configuration_version))
    return RouteOpportunity(
        route_id=f"route-{sha256(route_key.encode()).hexdigest()[:16]}",
        player_ids=player_ids,
        components=OpportunityComponents(
            lane_accessibility=accessibility,
            progression_value=max(-1.0, min(1.0, progression)),
            turnover_risk=turnover_risk,
            risk_penalty=risk_penalty,
        ),
        score=score,
    )


def state_opportunity(routes: tuple[RouteOpportunity, ...]) -> float:
    """Return U(S), or zero when no route is available."""

    return max((route.score for route in routes), default=0.0)


def score_triangle(
    triangle: TriangleCandidate,
    direct_lanes: tuple[LaneAccessibility, LaneAccessibility],
    routes: tuple[RouteOpportunity, ...],
    receiver_pressures: tuple[float, float],
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
) -> TacticalTriangleAnalysis:
    """Combine visible normalized components into the v0.1 heuristic score."""

    geometry_score = triangle.geometry.shape_quality if triangle.geometrically_valid else 0.0
    direct_lane_score = max(lane.accessibility for lane in direct_lanes)
    third_man_score = max(
        (route.components.lane_accessibility for route in routes if len(route.player_ids) == 3),
        default=0.0,
    )
    progression_score = max(
        (max(0.0, route.components.progression_value) for route in routes),
        default=0.0,
    )
    receiver_pressure_score = 1.0 - fmean(
        normalized_pressure(pressure, config) for pressure in receiver_pressures
    )
    components = TriangleScoreComponents(
        geometry=geometry_score,
        direct_lane=direct_lane_score,
        third_man=third_man_score,
        progression=progression_score,
        receiver_pressure=receiver_pressure_score,
    )
    weight_total = (
        config.triangle_geometry_weight
        + config.triangle_direct_lane_weight
        + config.triangle_third_man_weight
        + config.triangle_progression_weight
        + config.triangle_pressure_weight
    )
    weighted_score = (
        config.triangle_geometry_weight * components.geometry
        + config.triangle_direct_lane_weight * components.direct_lane
        + config.triangle_third_man_weight * components.third_man
        + config.triangle_progression_weight * components.progression
        + config.triangle_pressure_weight * components.receiver_pressure
    ) / weight_total
    heuristic_score = weighted_score if triangle.geometrically_valid else 0.0
    return TacticalTriangleAnalysis(
        triangle=triangle,
        direct_lanes=direct_lanes,
        routes=routes,
        score_components=components,
        heuristic_score=heuristic_score,
        tactically_useful=(
            triangle.geometrically_valid
            and heuristic_score >= config.minimum_tactical_triangle_score
        ),
        model_version=config.model_version,
        configuration_version=config.configuration_version,
    )
