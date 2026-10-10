"""Lightweight local benchmark for HANGO tactical engine v0.1."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

from app.fixtures import load_fixture
from app.models import Team
from app.tactical.engine import TacticalEngine
from app.tactical.gaussian_field import pressure_grid


def average_milliseconds(operation: Callable[[], object], iterations: int) -> float:
    start = perf_counter()
    for _ in range(iterations):
        operation()
    return (perf_counter() - start) * 1000.0 / iterations


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark HANGO tactical engine v0.1")
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--grid-iterations", type=int, default=5)
    args = parser.parse_args()
    if args.iterations < 1 or args.grid_iterations < 1:
        raise ValueError("benchmark iterations must be positive")

    fixture = load_fixture(Path("data/fixtures/positive-interaction.json"))
    engine = TacticalEngine()
    defenders = tuple(player for player in fixture.snapshot.players if player.team == Team.AWAY)

    engine.analyze_snapshot(fixture.snapshot, "H10", Team.HOME)
    engine.compute_interaction(
        fixture.snapshot,
        fixture.counterfactual,
        "H10",
        "H07",
        "H08",
        Team.HOME,
    )
    results = {
        "triangle_detection_ms": average_milliseconds(
            lambda: engine.detect_triangles(fixture.snapshot, "H10", Team.HOME),
            args.iterations,
        ),
        "pressure_grid_ms": average_milliseconds(
            lambda: pressure_grid(defenders, engine.config),
            args.grid_iterations,
        ),
        "full_snapshot_analysis_ms": average_milliseconds(
            lambda: engine.analyze_snapshot(fixture.snapshot, "H10", Team.HOME),
            args.iterations,
        ),
        "four_state_interaction_ms": average_milliseconds(
            lambda: engine.compute_interaction(
                fixture.snapshot,
                fixture.counterfactual,
                "H10",
                "H07",
                "H08",
                Team.HOME,
            ),
            args.iterations,
        ),
        "iterations": args.iterations,
        "grid_iterations": args.grid_iterations,
    }
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
