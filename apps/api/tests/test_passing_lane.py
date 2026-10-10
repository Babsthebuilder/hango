import pytest

from app.tactical.passing_lane import (
    is_in_passing_corridor,
    point_to_segment_distance,
    projection_parameter,
)


def test_projection_parameter_marks_segment_position() -> None:
    assert projection_parameter((4.0, 3.0), (0.0, 0.0), (10.0, 0.0)) == pytest.approx(0.4)


def test_point_to_segment_distance_clamps_to_endpoint() -> None:
    assert point_to_segment_distance((13.0, 4.0), (0.0, 0.0), (10.0, 0.0)) == pytest.approx(5.0)


def test_corridor_requires_lateral_and_longitudinal_inclusion() -> None:
    assert is_in_passing_corridor((4.0, 1.0), (0.0, 0.0), (10.0, 0.0), 1.5)
    assert not is_in_passing_corridor((4.0, 2.0), (0.0, 0.0), (10.0, 0.0), 1.5)
    assert not is_in_passing_corridor((12.0, 0.0), (0.0, 0.0), (10.0, 0.0), 1.5)


def test_zero_length_lane_fails_loudly() -> None:
    with pytest.raises(ValueError, match="non-zero length"):
        projection_parameter((1.0, 1.0), (0.0, 0.0), (0.0, 0.0))
