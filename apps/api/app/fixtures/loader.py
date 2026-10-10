"""Load fixture JSON through the external data contract."""

from __future__ import annotations

from pathlib import Path

from app.models import SyntheticFixture


def load_fixture(path: Path) -> SyntheticFixture:
    """Parse and validate one fixture file."""

    return SyntheticFixture.model_validate_json(path.read_text(encoding="utf-8"))


def validate_fixture_directory(directory: Path) -> tuple[Path, ...]:
    """Validate every JSON fixture and return the validated paths."""

    paths = tuple(sorted(directory.glob("*.json")))
    if not paths:
        raise ValueError(f"no JSON fixtures found in {directory}")
    for path in paths:
        load_fixture(path)
    return paths
