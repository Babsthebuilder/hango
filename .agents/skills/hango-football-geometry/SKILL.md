---
name: hango-football-geometry
description: Implement or review HANGO's deterministic football geometry, passing-lane primitives, defensive-pressure specification, route opportunity concepts, and four-state relational interaction algebra. Use for tactical mathematics, mathematical tests, or calculations over football snapshots; do not use for UI, Azure orchestration, or generative tactical values.
---

# HANGO Football Geometry

## Preserve the trusted boundary

- Calculate every trusted value with deterministic code. Never ask a generative model to supply a value.
- Keep the tactical core runnable without Azure.
- Version assumptions, thresholds, and model definitions.
- Label outputs `OBSERVED`, `CALCULATED`, `MODEL_ESTIMATE`, or `INTERPRETATION`.
- Reject causal or intent claims inferred only from positional coincidence.

## Use the coordinate system

Represent the pitch as the closed rectangle `[0, 105] x [0, 68]` metres. Require an explicit attacking direction for each team and reject off-pitch coordinates.

Use Euclidean distance and shoelace area. Calculate interior angles from clamped vector dot products. Reject zero-length sides, collinear/near-zero-area triangles, and triangles below the configured minimum angle. Keep thresholds configurable.

## Evaluate passing-lane geometry

For segment `A -> B` and point `D`, calculate projection parameter `t = ((D-A) dot (B-A)) / ||B-A||^2`. Clamp `t` only when finding point-to-segment distance. Treat a defender as inside a finite corridor only when `0 <= t <= 1` and distance is within the configured radius. Reject zero-length routes.

Do not turn geometric obstruction alone into a claim that a pass was impossible.

## Specify pressure and opportunity carefully

Use the Gaussian field `P_d(z) = w_d exp(-||z-p_d||^2 / (2 sigma_d^2))` and sum defender contributions when implementing the versioned pressure model. Describe it as a `MODEL_ESTIMATE`, not an observation or probability.

Treat `Q(r,S) = L(r,S) * DeltaV(r) - lambda R(r,S)` and `U(S) = max_r Q(r,S)` as provisional concepts until their components are empirically defined. Never claim that xT is goal probability unless a separately validated probability model supports that meaning.

## Calculate relational interaction

Evaluate a fixed opportunity function under four states:

- `U_00`: B baseline, C baseline.
- `U_10`: B moved, C baseline.
- `U_01`: B baseline, C moved.
- `U_11`: B moved, C moved.

Calculate `I_BC = U_11 - U_10 - U_01 + U_00`. Describe the result as modeled relational interaction or modeled complementarity. Never call it proven causal synergy.

Test positive, zero, and negative algebra cases independently of any production opportunity model. Mark any fake opportunity function as a test stub.
