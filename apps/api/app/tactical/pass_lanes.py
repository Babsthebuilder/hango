"""Continuous, geometry-only passing-lane accessibility analysis."""

from __future__ import annotations

from collections.abc import Iterable
from math import hypot

from app.models import PlayerState
from app.tactical.config import DEFAULT_TACTICAL_CONFIG, TacticalConfig
from app.tactical.geometry import Point, distance
from app.tactical.schemas import DefenderLaneMeasurement, LaneAccessibility


def projection_parameter(point: Point, start: Point, end: Point) -> float:
    """Project a point onto the infinite line through a directed segment."""

    segment = (end[0] - start[0], end[1] - start[1])
    length_squared = segment[0] ** 2 + segment[1] ** 2
    if length_squared == 0:
        raise ValueError("passing lane segment must have non-zero length")
    offset = (point[0] - start[0], point[1] - start[1])
    return (offset[0] * segment[0] + offset[1] * segment[1]) / length_squared


def point_to_segment_distance(point: Point, start: Point, end: Point) -> float:
    """Return distance to the closest point on a finite segment."""

    raw_parameter = projection_parameter(point, start, end)
    parameter = max(0.0, min(1.0, raw_parameter))
    closest = (
        start[0] + parameter * (end[0] - start[0]),
        start[1] + parameter * (end[1] - start[1]),
    )
    return hypot(point[0] - closest[0], point[1] - closest[1])


def is_in_passing_corridor(
    point: Point,
    start: Point,
    end: Point,
    corridor_radius: float,
) -> bool:
    """Check geometric inclusion in a finite constant-radius route corridor."""

    if corridor_radius < 0:
        raise ValueError("corridor radius must be non-negative")
    parameter = projection_parameter(point, start, end)
    clearance = point_to_segment_distance(point, start, end)
    return 0.0 <= parameter <= 1.0 and clearance <= corridor_radius


def _smooth_accessibility(clearance: float, clear_distance: float) -> float:
    """Smoothstep from fully obstructed at 0 m to fully clear at clear_distance."""

    ratio = max(0.0, min(1.0, clearance / clear_distance))
    return ratio * ratio * (3.0 - 2.0 * ratio)


def analyze_passing_lane(
    origin: PlayerState,
    target: PlayerState,
    defenders: Iterable[PlayerState],
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
) -> LaneAccessibility:
    """Return inspectable defender geometry and a continuous accessibility score."""

    start = (origin.position.x, origin.position.y)
    end = (target.position.x, target.position.y)
    pass_distance = distance(start, end)
    if pass_distance == 0:
        raise ValueError("candidate pass must have non-zero length")

    clear_distance = config.lane_corridor_radius_m + config.lane_falloff_m
    measurements: list[DefenderLaneMeasurement] = []
    relevant_clearances: list[tuple[str, float]] = []

    for defender in sorted(defenders, key=lambda player: player.player_id):
        point = (defender.position.x, defender.position.y)
        parameter = projection_parameter(point, start, end)
        clearance = point_to_segment_distance(point, start, end)
        relevant = 0.0 <= parameter <= 1.0
        factor = _smooth_accessibility(clearance, clear_distance) if relevant else 1.0
        intrusion = relevant and clearance <= config.lane_corridor_radius_m
        if relevant:
            relevant_clearances.append((defender.player_id, clearance))
        measurements.append(
            DefenderLaneMeasurement(
                defender_id=defender.player_id,
                projection_parameter=parameter,
                segment_distance_m=clearance,
                relevant_to_segment=relevant,
                corridor_intrusion=intrusion,
                accessibility_factor=factor,
            )
        )

    nearest = min(relevant_clearances, key=lambda item: (item[1], item[0]), default=None)
    accessibility = min(
        (measurement.accessibility_factor for measurement in measurements),
        default=1.0,
    )
    intruders = tuple(
        measurement.defender_id for measurement in measurements if measurement.corridor_intrusion
    )
    return LaneAccessibility(
        origin_id=origin.player_id,
        target_id=target.player_id,
        distance_m=pass_distance,
        accessibility=accessibility,
        nearest_relevant_defender_id=nearest[0] if nearest else None,
        minimum_clearance_m=nearest[1] if nearest else None,
        corridor_intruder_ids=intruders,
        defender_measurements=tuple(measurements),
    )
