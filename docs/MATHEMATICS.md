# HANGO Mathematical Specification v0.1

This document is the Phase 2 source of truth for tactical engine `tactical-v0.1`. All quantities use SI units and deterministic implementations. Thresholds are configuration, not hidden constants; model and assumption changes require a version change.

## 1. Coordinate system

The pitch is the closed rectangle `[0, 105] x [0, 68]` metres. The origin is one corner, `x` follows pitch length, and `y` follows pitch width. Each team declares whether it attacks toward increasing or decreasing `x`. Coordinates outside the rectangle are invalid.

## 2. Euclidean distance

For points `A = (x1, y1)` and `B = (x2, y2)`:

```text
d(A, B) = sqrt((x2 - x1)^2 + (y2 - y1)^2)
```

Distance is non-negative and invariant under rigid translation and rotation.

## 3. Triangle area

For `A = (x1, y1)`, `B = (x2, y2)`, and `C = (x3, y3)`:

```text
Area = 1/2 * abs(
  x1(y2 - y3)
  + x2(y3 - y1)
  + x3(y1 - y2)
)
```

The area is unsigned and expressed in square metres.

## 4. Interior angles

At vertex `A`, use vectors `u = B - A` and `v = C - A`:

```text
theta_A = arccos(clamp((u dot v) / (||u|| ||v||), -1, 1))
```

The other angles follow by permutation. A zero-length side is invalid. A valid non-degenerate triangle has an angle sum of 180 degrees within configured floating-point tolerance.

## 5. Validity constraints

A candidate triangle is valid only when:

- all three players are distinct and all coordinates are on-pitch;
- no side has zero length;
- area is at least configurable `minimum_area_m2`;
- every interior angle is at least configurable `minimum_angle_degrees`;
- optional minimum and maximum side-length rules, when used, are explicit and versioned.

The engine defaults to `minimum_area_m2 = 1.0`, `minimum_angle_degrees = 10.0`, a 35 m support radius, and 4 m minimum separation between support players. These are harness assumptions, not empirically proven football thresholds.

Shape quality is the normalized geometric measure:

```text
G = 4 sqrt(3) Area / (a^2 + b^2 + c^2)
```

It is zero for degenerate geometry and one for an equilateral triangle. It measures shape only, not tactical value.

## 6. Passing-lane projection

For route segment `A -> B` and defender point `D`, let `v = B - A`:

```text
t = ((D - A) dot v) / (v dot v)
projection_on_line = A + t v
t_segment = clamp(t, 0, 1)
closest_on_segment = A + t_segment v
distance_to_segment = ||D - closest_on_segment||
```

A defender is inside a simple route corridor when `0 <= t <= 1` and its point-to-segment distance is no greater than configured radius `c = 2 m`. A zero-length route is invalid. This geometric test is not, by itself, a conclusion that a pass is impossible.

For continuous accessibility, define clear distance `D = c + f`, where default falloff `f = 3 m`, and:

```text
x_d = clamp(clearance_d / D, 0, 1)
a_d = 3 x_d^2 - 2 x_d^3
L(r,S) = min relevant defenders a_d
```

Defenders with projections behind the passer or beyond the receiver do not reduce the finite-segment lane score. With no relevant defender, `L = 1`. This is a geometry-based accessibility score, never pass-completion probability.

## 7. Gaussian defensive-pressure field

For defender `d` at position `p_d`, evaluation point `z`, positive weight `w_d`, and positive spread `sigma_d`:

```text
P_d(z) = w_d * exp(-||z - p_d||^2 / (2 sigma_d^2))
P(z)   = sum_d P_d(z)
```

The implemented NumPy field defaults to `sigma = 4.5 m` and defender weight `1.0`. Both remain configurable. It supports arbitrary points, evenly sampled passing lanes, and deterministic whole-pitch grids. Weights, spreads, included defenders, and aggregation version must be recorded. `P(z)` is a `MODEL_ESTIMATE`, not an observation and not a probability.

## 8. Provisional route opportunity

For candidate route `r` in state `S`:

```text
Q(r, S) = L(r, S) * DeltaV(r) - lambda * R(r, S)
U(S)    = max_r Q(r, S)
```

- `L(r, S)` is the product of leg accessibility for a multi-leg route.
- `DeltaV(r)` is the signed change on the placeholder pitch-value surface.
- `R(r, S)` is the provisional turnover-risk heuristic.
- `lambda = 0.35` by default and remains configurable.

The uncalibrated linear pitch-value surface is:

```text
V_+(x) = x / 105                 when attacking toward increasing x
V_-(x) = (105 - x) / 105         when attacking toward decreasing x
DeltaV(r) = V(route end) - V(route start)
```

Normalize receiver pressure with scale `s = 2`:

```text
p_norm = P / (P + s)
R = [0.7 (1 - L) + 0.3 mean(p_norm on receivers)] / (0.7 + 0.3)
```

Every returned route exposes `L`, `DeltaV`, `R`, `lambda R`, and `Q`. Negative scores are allowed. The directed passing graph retains edges with `L >= 0.25` by default.

This is a provisional research heuristic only. `DeltaV` must not be described as goal probability unless a separately validated probability model actually defines it that way; this surface is not xT.

## 9. Tactical triangle heuristic

Geometrically valid triangles receive five visible component scores in `[0,1]`:

- geometry: normalized shape quality `G`;
- direct lane: best carrier-to-support accessibility;
- third man: best usable two-leg route accessibility;
- progression: best non-negative route `DeltaV`;
- receiver pressure: one minus mean normalized pressure at the two supports.

The default weighted score is:

```text
T = 0.15 geometry
  + 0.30 direct_lane
  + 0.25 third_man
  + 0.20 progression
  + 0.10 receiver_pressure
```

The weights sum to one and are configuration. Invalid geometry receives `T = 0`. The default tactical-usefulness threshold is `0.35`. `T` is an inspectable heuristic, not a learned probability or universal measure of football quality.

## 10. Four-state interaction

For supporting players `B` and `C`, evaluate the same opportunity function under four states:

- `U_00`: B baseline, C baseline.
- `U_10`: B moved, C baseline.
- `U_01`: B baseline, C moved.
- `U_11`: B moved, C moved.

Then:

```text
I_BC = U_11 - U_10 - U_01 + U_00
```

Positive, zero, and negative values indicate modeled super-additive, additive, and sub-additive interaction under the chosen model. Call this **modeled relational interaction** or **modeled complementarity**. Do not call it proven causal synergy.

The same route opportunity implementation and configuration are used in all four states. Values within `0.01` of zero are classified `NEUTRAL` by default; this tolerance is versioned configuration.

## 11. Terminology and claim restrictions

Every output must be classified as one of:

- `OBSERVED`: directly present in source event/tracking data.
- `CALCULATED`: deterministic result from observed or explicitly hypothetical inputs.
- `MODEL_ESTIMATE`: output whose meaning depends on a fitted or assumed model.
- `INTERPRETATION`: explanatory prose or tactical reading.

Do not infer causality or intent from positional coincidence. Do not let generative AI supply trusted numerical values. Every assumption, threshold, and model must be versioned, and every factual number must trace to deterministic inputs and a calculation reference.

## 12. Out-of-scope research

The following remain future research and must not be implied by the Phase 1 harness:

- learned or production xT/possession-value models;
- calibrated pass-completion or goal probabilities;
- player orientation, velocity, acceleration, and biomechanics;
- anisotropic and time-varying pressure fields;
- route travel time, ball physics, and interception dynamics;
- causal identification of off-ball effects;
- uncertainty intervals and empirical threshold calibration;
- full-match simulation, video-derived tracking, and 3D reconstruction.
