# Data Contracts v0.1

All external football state is validated by Pydantic v2 models in `apps/api/app/models/state.py`.

## Snapshot

A snapshot contains a schema version, stable snapshot ID, provenance, exactly 22 players, a ball state, and an explicit attacking direction for both teams. Player IDs are unique; each side has exactly 11 players; every coordinate lies inside the closed 105 m by 68 m pitch.

## CounterfactualState

A counterfactual references one baseline snapshot and supplies one or more player-position overrides. Overrides must reference players present in the baseline and remain inside the pitch. Baseline data is never mutated.

## Evidence contracts

`CalculationReference` identifies a deterministic calculation, its model version, source snapshot, and reproducible input hash. `ClaimEvidence` labels a claim as `OBSERVED`, `CALCULATED`, `MODEL_ESTIMATE`, or `INTERPRETATION`, records publication status, and carries its supporting calculation references.

These categories are not interchangeable. In particular, model estimates must not be presented as observations or deterministic calculations.

## Tactical calculation contracts

`apps/api/app/tactical/schemas.py` defines immutable, finite-number responses for triangle geometry, defender lane measurements, lane accessibility, pressure samples/grids, directed graph edges, opportunity components, tactical triangle scores, snapshot analyses, counterfactual comparisons, and four-state interaction.

Every composite score exposes its components. Tactical outputs carry `model_version` and `configuration_version`; interaction responses carry all four state utilities. NaN and infinity are rejected at the response boundary.
