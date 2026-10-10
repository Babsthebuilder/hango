---
name: hango-synthetic-fixtures
description: Create or validate deterministic HANGO football snapshot and counterfactual fixtures for geometry, passing-lane, evidence, and interaction tests. Use when authoring test data with 22 players, baseline and hypothetical positions, provenance, and plausible spacing; do not embed expected tactical answers in runtime fixtures.
---

# HANGO Synthetic Fixtures

## Build valid fixtures

- Include exactly 22 players and exactly 11 players per side.
- Use stable, unique player IDs and valid coordinates in `[0, 105] x [0, 68]` metres.
- Declare the attacking direction for both sides.
- Include an on-pitch ball state, schema version, and non-empty provenance.
- Keep a baseline snapshot immutable and express hypothetical positions as explicit overrides.
- Ensure every override references a baseline player and remains on-pitch.
- Use plausible football spacing; avoid coincident players unless invalid-state testing requires it.

Do not store final expected tactical scores, interaction values, or pass/fail answers in runtime data. Put expected outcomes in tests so the fixture remains input evidence rather than an oracle.

## Cover the three fixture classes

- `positive_relational_interaction`: make two supporting changes together plausibly offer more route value than either alone.
- `blocked_triangle`: keep the triangle geometrically valid while placing defenders to obstruct useful lanes.
- `neutral_interaction`: make individual supporting changes helpful but plausibly additive when combined.

Treat these labels as test-scenario intent, not a production-model verdict. A future opportunity evaluator must calculate its own result.

## Validate deterministically

Parse fixtures through the project Pydantic contracts. Fail loudly on wrong team counts, duplicate IDs, missing provenance, invalid directions, off-pitch states, or bad overrides. Keep ordering and serialization stable where snapshots are hashed.
