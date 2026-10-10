from math import cos, radians, sin

import pytest

from app.tactical.geometry import (
    TriangleThresholds,
    distance,
    interior_angles_degrees,
    is_valid_triangle,
    triangle_area,
    triangle_shape_quality,
)


def _translate(point: tuple[float, float], dx: float, dy: float) -> tuple[float, float]:
    return point[0] + dx, point[1] + dy


def _rotate(point: tuple[float, float], angle_degrees: float) -> tuple[float, float]:
    angle = radians(angle_degrees)
    return (
        point[0] * cos(angle) - point[1] * sin(angle),
        point[0] * sin(angle) + point[1] * cos(angle),
    )


def test_distance_uses_euclidean_geometry() -> None:
    assert distance((0.0, 0.0), (3.0, 4.0)) == pytest.approx(5.0)


def test_triangle_area_uses_shoelace_formula() -> None:
    assert triangle_area((0.0, 0.0), (4.0, 0.0), (0.0, 3.0)) == pytest.approx(6.0)


def test_interior_angles_sum_to_180_degrees() -> None:
    angles = interior_angles_degrees((0.0, 0.0), (4.0, 0.0), (0.0, 3.0))

    assert sum(angles) == pytest.approx(180.0)


def test_distance_and_area_are_translation_invariant() -> None:
    triangle = ((2.0, 3.0), (9.0, 4.0), (5.0, 11.0))
    translated = tuple(_translate(point, 17.0, -8.0) for point in triangle)

    assert distance(triangle[0], triangle[1]) == pytest.approx(
        distance(translated[0], translated[1])
    )
    assert triangle_area(*triangle) == pytest.approx(triangle_area(*translated))


def test_distance_and_area_are_rotation_invariant() -> None:
    triangle = ((2.0, 3.0), (9.0, 4.0), (5.0, 11.0))
    rotated = tuple(_rotate(point, 37.0) for point in triangle)

    assert distance(triangle[0], triangle[1]) == pytest.approx(
        distance(rotated[0], rotated[1])
    )
    assert triangle_area(*triangle) == pytest.approx(triangle_area(*rotated))


def test_collinear_triangle_is_rejected() -> None:
    assert not is_valid_triangle((0.0, 0.0), (5.0, 5.0), (10.0, 10.0))


def test_triangle_below_minimum_angle_is_rejected() -> None:
    thresholds = TriangleThresholds(minimum_area_m2=0.01, minimum_angle_degrees=10.0)

    assert not is_valid_triangle((0.0, 0.0), (10.0, 0.0), (9.9, 0.1), thresholds)


def test_equilateral_triangle_has_maximum_shape_quality() -> None:
    height = 3.0**0.5

    assert triangle_shape_quality((0.0, 0.0), (2.0, 0.0), (1.0, height)) == pytest.approx(1.0)


def test_non_finite_geometry_fails_loudly() -> None:
    with pytest.raises(ValueError, match="finite"):
        distance((float("nan"), 0.0), (1.0, 1.0))
