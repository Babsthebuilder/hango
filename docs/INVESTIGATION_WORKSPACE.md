# Visual investigation workspace

Phase 4 turns HANGO's deterministic tactical and evidence outputs into an inspectable broadcast-style workspace. The interface is a presentation client, not a second tactical engine.

## Workspace structure

The workspace has four persistent regions:

1. the header and pitch identify the fixture, both teams' attacking directions, and current evidence state;
2. the control rail switches observed/alternative/compare modes and reveals tactical layers in order;
3. the 105 × 68 metre pitch renders players, ball, direction, geometry, lanes, routes, and pressure;
4. the insight rail reports server-returned opportunity and score components and opens the evidence drawer.

The evidence drawer is loaded only when requested. It shows claim classification and decision, calculation identity, input/output hashes, model/configuration versions, lifecycle, provenance, and deterministic replay outcome.

The grounded explanation panel sits below the primary investigation stage so the pitch remains dominant. It shows provider-authored `INTERPRETATION` only after the editorial gate has returned a decision. Each sentence exposes one or more keyboard-accessible evidence citations that open the supporting calculation and claim in the evidence drawer.

## Coordinate mapping

Football coordinates remain in metres throughout application state and the SVG uses metre units. `toPitchPoint` maps x directly and flips y because SVG y increases downward:

```text
svgX = x
svgY = 68 - y
```

The pitch view box adds a two-unit visual margin around the 105 × 68 surface. The mapper rejects non-finite and out-of-bounds coordinates. This is deterministic presentation geometry only; triangle areas, passing lanes, pressure, route opportunity, scores, and interaction values arrive from the API.

## State comparison and layers

Observed state is solid cyan; alternative state is dashed amber and marked `HYPOTHETICAL`. Compare mode overlays movement vectors and both states. Counterfactual overrides are applied immutably, and the API returns the complete alternative tactical analysis.

Progressive reveal prevents the final score from obscuring its basis:

1. players and candidate triangle geometry;
2. direct passing lanes;
3. third-player routes;
4. tactical score components;
5. full investigation view.

Routes use line pattern, endpoint symbols, and text in addition to color. Lane accessibility is described as accessibility, never pass probability. Progression is a linear pitch-value component, never xT. Modeled interaction is not presented as proven causality.

## Modeled pressure

Pressure grids are computed by the Python tactical engine and returned with model and configuration versions. The client only maps the returned values to cells and normalizes their opacity relative to the largest returned value for legible rendering. Every pressure control, legend, and insight uses the `MODEL_ESTIMATE` classification. The field is not a calibrated probability or full pitch-control model.

## Epistemic and verification language

`OBSERVED`, `CALCULATED`, `MODEL_ESTIMATE`, and `INTERPRETATION` identify what kind of knowledge is being displayed. `SUPPORTED`, `QUALIFIED`, `REJECTED`, and `STALE` identify publication verification outcome. Lifecycle (`VALID`, `STALE`, or `INVALIDATED`) remains separate. Labels pair color with text and a distinct marker so meaning does not rely on color alone.

## States and accessibility

The application includes loading, empty-fixture, invalid-response, stale-evidence, replay-failure, explanation-loading, explanation-empty, provider-failure, and invalidated-prose presentations. Network and provider errors retain independent retry paths. The evidence drawer uses dialog semantics, moves focus on open, traps focus while open, closes with Escape, and restores focus to the citation or other trigger.

All controls are native buttons, radios, or checkboxes with visible focus indicators and accessible names. Pitch graphics include an SVG title and description, while changing summaries are announced through live regions. Layouts collapse for tablet and mobile widths. Motion is limited to short opacity/transform transitions and disabled when `prefers-reduced-motion: reduce` is active.

## Trust boundary

The browser may choose which authoritative result to show, transform metres into pixels, and format returned numbers. It must not calculate or verify tactical truth. New UI metrics require a typed backend contract, versioned calculation, evidence artifact, and verifier support before presentation.
