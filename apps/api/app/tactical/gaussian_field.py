"""Vectorized Gaussian defensive-pressure estimates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from app.models import PlayerState
from app.models.state import PITCH_LENGTH_METRES, PITCH_WIDTH_METRES
from app.tactical.config import DEFAULT_TACTICAL_CONFIG, TacticalConfig
from app.tactical.geometry import Point
from app.tactical.schemas import PressureGrid, PressureSamples

FloatArray = NDArray[np.float64]


def pressure_at_points(
    points: Sequence[Point] | FloatArray,
    defenders: Sequence[PlayerState],
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
    defender_weights: Mapping[str, float] | None = None,
) -> FloatArray:
    """Evaluate the summed isotropic Gaussian field at arbitrary points."""

    point_array = np.asarray(points, dtype=np.float64)
    if point_array.ndim != 2 or point_array.shape[1] != 2:
        raise ValueError("points must have shape (n, 2)")
    if not np.isfinite(point_array).all():
        raise ValueError("pressure points must be finite")
    if not defenders:
        return np.zeros(point_array.shape[0], dtype=np.float64)

    defender_positions = np.asarray(
        [(player.position.x, player.position.y) for player in defenders],
        dtype=np.float64,
    )
    weights = np.asarray(
        [
            defender_weights.get(player.player_id, config.default_defender_weight)
            if defender_weights is not None
            else config.default_defender_weight
            for player in defenders
        ],
        dtype=np.float64,
    )
    if not np.isfinite(weights).all() or np.any(weights < 0):
        raise ValueError("defender weights must be finite and non-negative")

    offsets = point_array[:, np.newaxis, :] - defender_positions[np.newaxis, :, :]
    squared_distances = np.sum(offsets * offsets, axis=2)
    contributions = weights[np.newaxis, :] * np.exp(
        -squared_distances / (2.0 * config.pressure_sigma_m**2)
    )
    return np.sum(contributions, axis=1, dtype=np.float64)


def pressure_at_point(
    point: Point,
    defenders: Sequence[PlayerState],
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
    defender_weights: Mapping[str, float] | None = None,
) -> float:
    """Evaluate pressure at one point."""

    return float(pressure_at_points([point], defenders, config, defender_weights)[0])


def pressure_along_lane(
    start: Point,
    end: Point,
    defenders: Sequence[PlayerState],
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
    defender_weights: Mapping[str, float] | None = None,
) -> PressureSamples:
    """Evaluate pressure at evenly spaced samples along a candidate pass."""

    parameters = np.linspace(0.0, 1.0, config.pressure_lane_samples, dtype=np.float64)
    start_array = np.asarray(start, dtype=np.float64)
    end_array = np.asarray(end, dtype=np.float64)
    points = start_array + parameters[:, np.newaxis] * (end_array - start_array)
    values = pressure_at_points(points, defenders, config, defender_weights)
    value_tuple = tuple(float(value) for value in values)
    return PressureSamples(
        at_origin=value_tuple[0],
        at_target=value_tuple[-1],
        along_lane=value_tuple,
        maximum_along_lane=max(value_tuple),
        mean_along_lane=float(np.mean(values)),
    )


def pressure_grid(
    defenders: Sequence[PlayerState],
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
    defender_weights: Mapping[str, float] | None = None,
) -> PressureGrid:
    """Evaluate the field over a deterministic whole-pitch grid."""

    x_coordinates = _pitch_axis(PITCH_LENGTH_METRES, config.pressure_grid_step_m)
    y_coordinates = _pitch_axis(PITCH_WIDTH_METRES, config.pressure_grid_step_m)
    x_mesh, y_mesh = np.meshgrid(x_coordinates, y_coordinates)
    points = np.column_stack((x_mesh.ravel(), y_mesh.ravel()))
    values = pressure_at_points(points, defenders, config, defender_weights).reshape(y_mesh.shape)
    return PressureGrid(
        x_coordinates=tuple(float(value) for value in x_coordinates),
        y_coordinates=tuple(float(value) for value in y_coordinates),
        values=tuple(tuple(float(value) for value in row) for row in values),
    )


def _pitch_axis(maximum: float, step: float) -> FloatArray:
    values = np.arange(0.0, maximum, step, dtype=np.float64)
    if values.size == 0 or values[-1] != maximum:
        values = np.append(values, maximum)
    return values
