"""Backward-compatible import surface for Phase 1 callers."""

from app.tactical.pass_lanes import (
    analyze_passing_lane,
    is_in_passing_corridor,
    point_to_segment_distance,
    projection_parameter,
)

__all__ = [
    "analyze_passing_lane",
    "is_in_passing_corridor",
    "point_to_segment_distance",
    "projection_parameter",
]
