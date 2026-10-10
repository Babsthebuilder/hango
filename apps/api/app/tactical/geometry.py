"""Deterministic geometry primitives for tactical engine v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, degrees, hypot, isfinite, sqrt

from app.tactical.schemas import InteriorAngles, SideLengths, TriangleGeometry

type Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class TriangleThresholds:
    """Explicit harness thresholds; not empirically calibrated football truth."""

    minimum_area_m2: float = 1.0
    minimum_angle_degrees: float = 10.0

    def __post_init__(self) -> None:
        if self.minimum_area_m2 < 0:
            raise ValueError("minimum area must be non-negative")
        if not 0 <= self.minimum_angle_degrees < 60:
            raise ValueError("minimum angle must be in [0, 60) degrees")


DEFAULT_TRIANGLE_THRESHOLDS = TriangleThresholds()


def distance(first: Point, second: Point) -> float:
    """Return Euclidean distance in metres."""

    _require_finite_points(first, second)
    return hypot(second[0] - first[0], second[1] - first[1])


def triangle_area(first: Point, second: Point, third: Point) -> float:
    """Return unsigned triangle area in square metres."""

    _require_finite_points(first, second, third)
    return 0.5 * abs(
        first[0] * (second[1] - third[1])
        + second[0] * (third[1] - first[1])
        + third[0] * (first[1] - second[1])
    )


def _angle_degrees(vertex: Point, arm_one: Point, arm_two: Point) -> float:
    _require_finite_points(vertex, arm_one, arm_two)
    vector_one = (arm_one[0] - vertex[0], arm_one[1] - vertex[1])
    vector_two = (arm_two[0] - vertex[0], arm_two[1] - vertex[1])
    magnitude_one = hypot(*vector_one)
    magnitude_two = hypot(*vector_two)
    if magnitude_one == 0 or magnitude_two == 0:
        raise ValueError("triangle sides must have non-zero length")
    cosine = (
        vector_one[0] * vector_two[0] + vector_one[1] * vector_two[1]
    ) / (magnitude_one * magnitude_two)
    return degrees(acos(max(-1.0, min(1.0, cosine))))


def interior_angles_degrees(first: Point, second: Point, third: Point) -> tuple[float, ...]:
    """Return the three interior angles in vertex order."""

    return (
        _angle_degrees(first, second, third),
        _angle_degrees(second, first, third),
        _angle_degrees(third, first, second),
    )


def triangle_shape_quality(first: Point, second: Point, third: Point) -> float:
    """Return a scale-invariant shape score: 0 degenerate, 1 equilateral."""

    side_lengths = (
        distance(first, second),
        distance(first, third),
        distance(second, third),
    )
    denominator = sum(side * side for side in side_lengths)
    if denominator == 0:
        return 0.0
    quality = 4.0 * sqrt(3.0) * triangle_area(first, second, third) / denominator
    return max(0.0, min(1.0, quality))


def calculate_triangle_geometry(first: Point, second: Point, third: Point) -> TriangleGeometry:
    """Return all geometry for one ordered carrier/support triangle."""

    lengths = SideLengths(
        carrier_to_b_m=distance(first, second),
        carrier_to_c_m=distance(first, third),
        b_to_c_m=distance(second, third),
    )
    try:
        angle_values = interior_angles_degrees(first, second, third)
    except ValueError:
        angle_values = (0.0, 0.0, 0.0)
    angles = InteriorAngles(
        carrier_degrees=angle_values[0],
        b_degrees=angle_values[1],
        c_degrees=angle_values[2],
    )
    return TriangleGeometry(
        distances=lengths,
        angles=angles,
        area_m2=triangle_area(first, second, third),
        shape_quality=triangle_shape_quality(first, second, third),
    )


def _require_finite_points(*points: Point) -> None:
    if not all(isfinite(coordinate) for point in points for coordinate in point):
        raise ValueError("geometry coordinates must be finite")


def is_valid_triangle(
    first: Point,
    second: Point,
    third: Point,
    thresholds: TriangleThresholds = DEFAULT_TRIANGLE_THRESHOLDS,
) -> bool:
    """Check deterministic area and minimum-angle validity filters."""

    if triangle_area(first, second, third) < thresholds.minimum_area_m2:
        return False
    try:
        angles = interior_angles_degrees(first, second, third)
    except ValueError:
        return False
    return min(angles) >= thresholds.minimum_angle_degrees
