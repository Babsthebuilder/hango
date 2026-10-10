# Data Contracts v0.1

All external football state is validated by Pydantic v2 models in `apps/api/app/models/state.py`.

## Snapshot

A snapshot contains a schema version, stable snapshot ID, provenance, exactly 22 players, a ball state, and an explicit attacking direction for both teams. Player IDs are unique; each side has exactly 11 players; every coordinate lies inside the closed 105 m by 68 m pitch.

## CounterfactualState

A counterfactual references one baseline snapshot and supplies one or more player-position overrides. Overrides must reference players present in the baseline and remain inside the pitch. Baseline data is never mutated.

## Evidence contracts

Evidence contracts live in `apps/api/app/evidence/models.py` and are immutable Pydantic v2 models.

`EvidenceReference` identifies one source by stable reference/object IDs, evidence kind, SHA-256 content hash, snapshot/calculation IDs when applicable, model version, provenance, schema version, and lifecycle state.

`CalculationReference` identifies a deterministic calculation by calculation kind, input/output hashes, snapshot ID, model and configuration versions, schema version, source references, and lifecycle state. `CalculationArtifact` stores that reference with replay inputs, authoritative output, complete configuration, and units for numerical output paths.

`ClaimEvidence` records claim ID/text, claim type and evidence classification, evidence and calculation references, numerical assertions, model version, current verification result and reason, provenance links, lifecycle state, and schema version. `ClaimRecord` adds append-only verification history.

`ReplayResult` contains output hashes, numeric differences, version/configuration matches, stale dependencies, and an explanation. `VerificationResult` contains exactly one of `SUPPORTED`, `QUALIFIED`, `REJECTED`, or `STALE`.

These categories are not interchangeable. In particular, model estimates must not be presented as observations or deterministic calculations.

Lifecycle values are `VALID`, `STALE`, and `INVALIDATED`. Lifecycle describes evidence history; verification status describes whether a claim is currently publishable.

## Tactical calculation contracts

`apps/api/app/tactical/schemas.py` defines immutable, finite-number responses for triangle geometry, defender lane measurements, lane accessibility, pressure samples/grids, directed graph edges, opportunity components, tactical triangle scores, snapshot analyses, counterfactual comparisons, and four-state interaction.

Every composite score exposes its components. Tactical outputs carry `model_version` and `configuration_version`; interaction responses carry all four state utilities. NaN and infinity are rejected at the response boundary.

### Investigation transport contracts

`CompareRequest` combines a validated snapshot, a counterfactual override set, the ball carrier, and attacking team. The response is a `CounterfactualComparison` containing complete baseline and alternative `SnapshotAnalysis` objects plus the server-calculated opportunity delta.

`PressureGridRequest` combines a snapshot and attacking team with an optional counterfactual. `PressureGridComparison` returns a baseline `PressureGridResult` and, when requested, an alternative result. Every grid result carries `MODEL_ESTIMATE`, tactical model version, and configuration version; it is not a probability or causal surface.

`POST /api/evidence/calculations/snapshot-analysis` accepts `AnalyzeRequest`, runs the existing tactical engine, registers the replayable artifact, and returns `CalculationDetails`. This endpoint gives investigation clients hashes and provenance without recreating artifact construction in the browser.

## Explanation contracts

Explanation contracts live in `apps/api/app/explanations/models.py` and use `explanation-schema-v0.1`.

`ExplanationRequest` requires at least one registered calculation ID and one registered claim ID. It selects a configured provider but cannot supply tactical facts directly.

`EvidenceCitation` links one sentence to a claim. A numerical citation additionally requires a calculation ID, output field path, unit, and authoritative numeric value. `ExplanationSentence` requires at least one citation and validates citation ownership.

`ExplanationDraft` contains unique sentences, provider identity/version, and the fixed `INTERPRETATION` classification. It contains no verification or publication authority.

`EditorialVerificationResult` contains exactly one evidence-style status, a derived `publishable` flag, reasons, checked IDs, and offending sentence IDs. Only `SUPPORTED` and `QUALIFIED` can be publishable.

`ExplanationArtifact` stores the request, draft, current deterministic decision, append-only verification history, evidence validity, and publication state. Publication states are `DRAFT`, `READY`, `BLOCKED`, `STALE`, and `INVALIDATED`; they do not replace evidence lifecycle or verification status.
