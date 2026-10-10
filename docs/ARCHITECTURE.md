# Architecture

## Principles

The trusted core is a deterministic Python library inside the FastAPI application. It accepts validated state, performs versioned calculations, and emits references that can be traced back to inputs. It has no Azure dependency.

```text
validated snapshot
       |
       v
triangle detector ---> lane analysis ---> directed passing graph
       |                    |                       |
       v                    v                       v
structured geometry   Gaussian pressure      route opportunity
       |                    |                       |
       +--------------------+-----------------------+
                            v
                  tactical score / interaction
                            |
                            v
                calculation artifact
                            |
                            v
             evidence registry / replay
                            |
                            v
                 verified claim ---> grounded explanation
                                             |
                                             v
                                  editorial verification ---> FastAPI
```

Microsoft Foundry may later consume deterministic outputs to coordinate Analyst, Narrator, and Verifier workflows. It must never become the source of trusted geometry or numerical tactical metrics, and generated prose must not self-verify.

## Monorepo boundaries

- `apps/api/app/models`: external contracts.
- `apps/api/app/tactical`: deterministic mathematics.
- `apps/api/app/evidence`: canonical hashing, evidence models, dependency graph, in-memory registry, deterministic replay, and claim verification.
- `apps/api/app/explanations`: evidence retrieval, provider-neutral narration, deterministic editorial verification, and explanation lifecycle.
- `apps/api/app/fixtures`: fixture loading and validation.
- `apps/api/app/routes`: transport-only FastAPI routes.
- `apps/web`: presentation; no trusted calculations.
- `data/fixtures`: input states without embedded expected answers.

## Tactical v0.1 modules

- `geometry.py`: finite Euclidean and triangle calculations.
- `triangle_detector.py`: deterministic same-team candidate generation.
- `pass_lanes.py`: segment geometry and continuous accessibility.
- `gaussian_field.py`: vectorized modeled pressure at points, lanes, and grids.
- `passing_graph.py`: directed edges and third-player route availability.
- `opportunity.py`: linear pitch value, provisional risk, route and triangle scores.
- `interaction.py`: four-state algebra and tolerance-based sign classification.
- `engine.py`: snapshot, triangle, counterfactual, and interaction orchestration.
- `schemas.py` and `config.py`: immutable finite outputs and versioned constants.

No tactical module imports Azure, Foundry, a network client, or a generative model.

## Evidence v0.1 modules

- `models.py`: immutable evidence, calculation, claim, replay, verification, and lifecycle contracts.
- `config.py`: versioned canonicalization and numeric-comparison policy.
- `hashing.py`: semantic normalization, canonical UTF-8 JSON, and SHA-256 wrappers.
- `dependency_graph.py`: cycle-safe upstream/downstream graph traversal.
- `registry.py`: replaceable repository interface and audit-preserving in-memory implementation.
- `replay.py`: calculation artifact construction, tactical dispatch, and tolerance-aware comparison.
- `verification.py`: deterministic claim publication rules.
- `schemas.py`: typed evidence API request and response contracts.

The evidence service depends on the tactical engine to replay trusted calculations. The tactical engine does not depend on evidence or publication concerns. HTTP routes remain transport adapters around these services.

## Explanation v0.1 modules

- `models.py`: immutable requests, sentence citations, drafts, artifacts, editorial decisions, and publication lifecycle.
- `analyst.py`: read-only retrieval of registered calculations and claims.
- `providers.py`: provider interface and deterministic offline template provider.
- `narrator.py`: composition boundary that always emits `INTERPRETATION` and never a decision.
- `verification.py`: deterministic source, wording, number, unit, and lifecycle checks.
- `registry.py`: audit-preserving in-memory explanation persistence.
- `service.py`: Analyst → Narrator → Editorial Verifier orchestration.
- `routes/explanations.py`: typed generate, retrieve, verify, and invalidate endpoints.

The Editorial Verifier invokes the existing claim verifier and deterministic replay path. It does not trust provider citations until they match a registered claim assertion and authoritative calculation output. Generated or interpretive prose cannot be used as an upstream evidence source.

## Investigation workspace

The Phase 4 React client is a projection of API-owned state and evidence:

```text
validated fixture ─┬─> counterfactual comparison ─> pitch and insight rail
                  ├─> modeled pressure grid ──────> display-only field
                  └─> calculation artifact ──────> verified claim
                                                     │
                                                     └─> evidence drawer / replay
```

`api.ts` owns typed transport, `geometry.ts` owns deterministic metre-to-SVG presentation mapping, and `InvestigationWorkspace.tsx` owns view state. `Pitch.tsx` renders the state and progressive tactical layers; `EvidenceDrawer.tsx` is lazy-loaded and presents the authoritative evidence record. Components receive typed server results and do not import tactical formulas.

`ExplanationPanel.tsx` owns explanation loading, failure, retry, empty, stale, invalidated, and ready states. Its sentence citations open the existing evidence drawer so editorial prose never becomes a disconnected trust surface.

Actual and alternative states share the same immutable baseline fixture. The alternative is materialized by the API and displayed with dashed amber marks and a `HYPOTHETICAL` label; the observed state uses solid cyan marks and an `OBSERVED` label. The frontend may format, filter, and normalize values for pixels or color opacity, but it may not derive trusted geometry, tactical scores, modeled interaction, or publication decisions.

## Deployment posture

The local engine, provider, and tests run without network access after dependencies are installed. `infra/azure` is intentionally reserved. Azure CLI authentication was available during Phase 5, but no Foundry project endpoint, model deployment, or relevant installed implementation skill was present. A future Foundry integration must implement the existing provider interface and remain an adapter around the core.
