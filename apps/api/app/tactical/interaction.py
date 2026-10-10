"""Four-state modeled relational interaction calculations."""

from app.tactical.config import DEFAULT_TACTICAL_CONFIG, TacticalConfig
from app.tactical.schemas import InteractionResult, InteractionSign


def four_state_interaction(u_00: float, u_10: float, u_01: float, u_11: float) -> float:
    """Return I = U11 - U10 - U01 + U00 for precomputed opportunities."""

    return u_11 - u_10 - u_01 + u_00


def classify_interaction(
    interaction: float,
    tolerance: float,
) -> InteractionSign:
    """Classify modeled interaction using an explicit neutral tolerance."""

    if tolerance < 0:
        raise ValueError("neutral tolerance must be non-negative")
    if interaction > tolerance:
        return InteractionSign.POSITIVE
    if interaction < -tolerance:
        return InteractionSign.NEGATIVE
    return InteractionSign.NEUTRAL


def build_interaction_result(
    u_00: float,
    u_10: float,
    u_01: float,
    u_11: float,
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
) -> InteractionResult:
    """Return all four utilities, algebra result, and non-causal sign label."""

    value = four_state_interaction(u_00, u_10, u_01, u_11)
    return InteractionResult(
        u_00=u_00,
        u_10=u_10,
        u_01=u_01,
        u_11=u_11,
        interaction_value=value,
        sign=classify_interaction(value, config.interaction_neutral_tolerance),
        model_version=config.model_version,
        configuration_version=config.configuration_version,
    )
