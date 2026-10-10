# Evidence and verification

HANGO separates deterministic computation, evidence lifecycle, and publication approval. The evidence engine is local, replayable, and independent of Azure or generated prose.

## Authority hierarchy

```text
football state
      -> deterministic calculation
      -> evidence artifact
      -> verified claim
      -> AI explanation
      -> studio publication
```

Authority only flows from left to right. Generated or edited prose cannot enter the registry as deterministic authority and cannot approve itself. A later agent may recommend wording, but only the deterministic verifier assigns a publication status.

Phase 5 implements this boundary with separate Analyst, Narrator, and Editorial Verifier classes. The narrator provider returns prose and citations only. The verifier independently resolves every citation against current registered evidence and assigns the decision.

## Evidence chain example

```text
Snapshot
  -> TriangleAnalysis
  -> InteractionResult
  -> ClaimEvidence
  -> VerifiedClaim
```

Each arrow is a stored dependency edge. Changing a snapshot, model, configuration, or schema makes affected downstream calculations and claims `STALE`. Explicitly invalidating an upstream item transitively invalidates its dependents. No operation silently deletes historical evidence.

## Canonical serialization and hashes

`app.evidence.hashing` converts supported values to canonical UTF-8 JSON before SHA-256 hashing:

- dictionary keys are sorted;
- enums use their stable string values;
- timezone-aware datetimes are converted to UTC with a `Z` suffix;
- semantically unordered collections, including snapshot players and evidence references, are sorted by stable identity;
- no runtime paths, memory identities, random UUIDs, or creation timestamps are added;
- claim hashes exclude mutable verification status, reason, and lifecycle state.

Snapshots, counterfactuals, tactical configuration, triangles, route opportunities, tactical analyses, interactions, and claim evidence use the same canonical hash boundary.

### Float normalization

Floats are converted through decimal text and quantized with round-half-even to nine decimal places. The fixed-width decimal string is then hashed. Nine decimal places retain sub-millimetre spatial distinctions and score changes far below the engine's tactical thresholds while avoiding irrelevant binary-float formatting differences. The precision is versioned in `EvidenceConfig`.

Hash normalization does not change authoritative runtime values. Replay and numerical-claim verification compare floats with the separately configured absolute and relative tolerances, both `1e-9` in `evidence-config-v0.1`.

## Calculation identity and artifacts

A calculation reference has this stable form:

```text
calc:<calculation-kind>:<first-20-hex-characters-of-identity-sha256>
```

The identity digest includes calculation kind, input hash, output hash, tactical model version, tactical configuration version, and evidence schema version. Registry insertion validates all hashes and rejects a same-ID/different-artifact collision.

`CalculationArtifact` preserves:

- the `CalculationReference`;
- canonical replay inputs;
- authoritative output;
- the complete tactical configuration;
- units for claimable numerical paths.

Supported replay kinds in Phase 3 are snapshot analysis, tactical triangle analysis, and four-state interaction.

## Claim evidence

`ClaimEvidence` stores the claim ID and text, its `OBSERVED`, `CALCULATED`, `MODEL_ESTIMATE`, or `INTERPRETATION` classification, evidence and calculation references, numerical assertions with units and output paths, model and schema versions, verification result and reason, provenance links, and lifecycle state.

`ClaimRecord` wraps that evidence with an append-only verification history. Publication status and lifecycle state remain separate:

- `SUPPORTED`: current evidence fully supports the wording and numbers;
- `QUALIFIED`: deterministic evidence supports only narrower or explicitly interpretive wording;
- `REJECTED`: evidence is missing, contradictory, invalidated, numerically wrong, self-referential, or materially overclaimed;
- `STALE`: the claim was supportable but an input, version, schema, or dependency must be revalidated.

## `STALE` versus `INVALIDATED`

`STALE` means an artifact may have been historically valid, but it is not current enough for publication. Replay or revalidation can produce a new current artifact.

`INVALIDATED` means the artifact is explicitly untrustworthy and cannot support current evidence. It remains stored for audit history. A claim depending on invalidated evidence receives `REJECTED`, not `STALE`.

## Replay

Replay retrieves the stored input and tactical configuration, dispatches the same deterministic tactical operation, and compares the result with the authoritative output. `ReplayResult` reports expected and actual hashes, numeric differences, version/configuration matches, stale dependencies, and a plain-language explanation.

An exact replay produces the same content hash. Numeric leaves are also compared with `math.isclose` using versioned tolerances. A changed input, model, or configuration marks the calculation and its dependents stale. A mismatch from the same current inputs and configuration invalidates the calculation because the deterministic contract has been broken.

## Verification rules

The verifier checks that:

1. the claim schema is current and referenced snapshot schemas are compatible;
2. every source and calculation exists;
3. references match stored hashes and versions;
4. no dependency is stale or invalidated;
5. deterministic replay succeeds;
6. each numerical assertion resolves to an authoritative output path;
7. value and unit match within configured tolerance;
8. claim type matches its evidence classification;
9. observed claims do not depend on calculated output;
10. wording does not convert modeled values into observations or probabilities;
11. intent or causal language is qualified unless evidence specifically supports it;
12. generated prose is never treated as evidence.

The current tactical engine has no calibrated goal-probability model. Claims such as “34% chance of a goal” are rejected. Lane accessibility is not pass-completion probability, linear pitch value is not xT, and modeled interaction is not proven causal synergy.

## Dependency registry

`EvidenceRegistry` defines a replaceable persistence boundary. `InMemoryEvidenceRegistry` stores calculations, claims, source references, dependency edges, and lifecycle audit transitions. It supports direct and transitive dependency lookup, cycle detection, deterministic replay, staleness propagation, and invalidation propagation. Phase 3 deliberately adds no database.

## Editorial verification

Before an explanation is marked `READY`, the editorial verifier:

1. requires the draft to remain `INTERPRETATION`;
2. re-verifies every registered source claim, including deterministic calculation replay;
3. rejects claims whose lifecycle is stale, invalidated, or rejected;
4. rejects generated or interpretive claims used as authoritative evidence;
5. requires every sentence to carry a registered claim citation;
6. requires every displayed number to match a citation at its explicit display precision;
7. requires each numeric citation to match a claim assertion, calculation output path, and unit;
8. rejects calibrated-probability wording, xT terminology, unsupported causality, and unsupported intent;
9. inherits `QUALIFIED` when a permitted source is explicitly qualified;
10. permits publication only for `SUPPORTED` or `QUALIFIED` decisions.

Explanation retrieval re-runs this gate, so changed upstream lifecycle is surfaced as `STALE` or `INVALIDATED` without silently deleting prose. Explicit invalidation preserves prior verification history.

## Automated verification

`scripts/verify.sh` validates fixtures, runs Ruff, executes Pytest, runs the Vitest frontend suite, and type-checks/builds the frontend. Evidence tests cover canonical serialization, content hashes, stable calculation IDs, collision handling, registry retrieval, cycle detection, exact and changed-input replay, model/configuration staleness, tolerance behavior, units, all claim outcomes, unsupported intent/causality, prose self-verification, transitive propagation, API behavior, and the complete synthetic-fixture evidence chain.

Frontend tests cover metre-to-SVG coordinate mapping and bounds, immutable player overrides, observed/alternative visual distinction, progressive layer toggles, modeled-pressure labeling, evidence retrieval and replay, drawer keyboard behavior, and verification-status presentation. These tests assert presentation behavior only; tactical correctness remains covered by Python engine and API tests.

Phase 5 tests additionally cover provider-neutral generation, sentence citations, exact and rounded numbers, missing citations, unsupported numbers, probability/xT/causal overclaiming, qualified publication, prose self-reference, stale dependencies, provider failure, explanation API lifecycle, panel retry, invalidated presentation, keyboard citation activation, and evidence-drawer retrieval.

Run:

```bash
bash ./scripts/verify.sh
```
