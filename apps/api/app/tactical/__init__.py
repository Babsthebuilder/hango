"""Deterministic tactical mathematics."""

from app.tactical.geometry import (
    TriangleThresholds,
    calculate_triangle_geometry,
    distance,
    interior_angles_degrees,
    is_valid_triangle,
    triangle_area,
    triangle_shape_quality,
)
from app.tactical.interaction import (
    build_interaction_result,
    classify_interaction,
    four_state_interaction,
)
from app.tactical.pass_lanes import (
    analyze_passing_lane,
    is_in_passing_corridor,
    point_to_segment_distance,
    projection_parameter,
)

__all__ = [
    "TriangleThresholds",
    "analyze_passing_lane",
    "build_interaction_result",
    "calculate_triangle_geometry",
    "classify_interaction",
    "distance",
    "four_state_interaction",
    "interior_angles_degrees",
    "is_in_passing_corridor",
    "is_valid_triangle",
    "point_to_segment_distance",
    "projection_parameter",
    "triangle_area",
    "triangle_shape_quality",
]
