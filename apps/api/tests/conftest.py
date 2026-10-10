from pathlib import Path

import pytest

from app.fixtures import load_fixture
from app.models import SyntheticFixture

FIXTURE_DIRECTORY = Path(__file__).parents[3] / "data" / "fixtures"


@pytest.fixture
def positive_fixture() -> SyntheticFixture:
    return load_fixture(FIXTURE_DIRECTORY / "positive-interaction.json")


@pytest.fixture
def blocked_fixture() -> SyntheticFixture:
    return load_fixture(FIXTURE_DIRECTORY / "blocked-triangle.json")


@pytest.fixture
def neutral_fixture() -> SyntheticFixture:
    return load_fixture(FIXTURE_DIRECTORY / "neutral-interaction.json")
