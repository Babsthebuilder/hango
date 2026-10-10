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
                         FastAPI
```

Microsoft Foundry may later consume deterministic outputs to coordinate Analyst, Narrator, and Verifier workflows. It must never become the source of trusted geometry or numerical tactical metrics, and generated prose must not self-verify.

## Monorepo boundaries

- `apps/api/app/models`: external contracts.
- `apps/api/app/tactical`: deterministic mathematics.
- `apps/api/app/evidence`: evidence verification (future implementation).
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

## Deployment posture

The local engine and tests run without network access after dependencies are installed. `infra/azure` is intentionally reserved. Azure services will be adapters around the core, not dependencies of it.
