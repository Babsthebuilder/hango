# HANGO

HANGO reveals and verifies the hidden relational geometry behind decisive football moments.

This Phase 0–5 repository provides an offline-first monorepo foundation, validated data contracts, synthetic fixtures, a deterministic tactical engine, canonical evidence hashing, replayable calculation artifacts, transitive provenance, deterministic claim and editorial verification, provider-neutral grounded explanations, typed FastAPI endpoints, and a responsive React investigation workspace. It deliberately does not implement a calibrated xT model, full pitch control, Foundry agents, autonomous publication, or Azure deployment.

## Prerequisites

- Python 3.12 or newer (the project is targeted at Python 3.12)
- Node.js and npm
- Bash (Git Bash is sufficient on Windows)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
npm --prefix apps/web install
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Verify

```bash
bash ./scripts/verify.sh
```

Run the API locally with `uvicorn app.main:app --app-dir apps/api --reload` and the frontend with `npm --prefix apps/web run dev`. On Windows, invoke verification from Git Bash (WSL is not required).

Run the lightweight engine benchmark with:

```bash
python scripts/benchmark.py
```

## Tactical API

- `GET /health`
- `GET /api/fixtures`
- `GET /api/fixtures/{fixture_id}`
- `POST /api/tactical/analyze`
- `POST /api/tactical/compare`
- `POST /api/tactical/pressure-grid`
- `POST /api/tactical/interaction`
- `POST /api/evidence/calculations/snapshot-analysis`
- `POST /api/evidence/register`
- `GET /api/evidence/calculations/{calculation_id}`
- `GET /api/evidence/claims/{claim_id}`
- `POST /api/evidence/verify`
- `POST /api/evidence/replay`
- `POST /api/evidence/invalidate`
- `POST /api/evidence/stale`
- `POST /api/explanations/generate`
- `GET /api/explanations/{explanation_id}`
- `POST /api/explanations/{explanation_id}/verify`
- `POST /api/explanations/{explanation_id}/invalidate`

Example analysis request:

```json
{
  "snapshot": {"...": "validated Snapshot contract"},
  "ball_carrier_id": "H10",
  "attacking_team": "HOME"
}
```

Example interaction request:

```json
{
  "snapshot": {"...": "validated Snapshot contract"},
  "counterfactual": {"...": "validated CounterfactualState contract"},
  "ball_carrier_id": "H10",
  "support_b_id": "H07",
  "support_c_id": "H08",
  "attacking_team": "HOME"
}
```

All tactical values are deterministic calculations or explicitly labeled provisional model estimates. Lane accessibility is not pass-completion probability, linear pitch value is not xT, and interaction is not a causal claim.

## Investigation workspace

The web application loads a validated synthetic fixture and requests comparison, pressure, calculation, and verification artifacts from the API. Its 105 × 68 metre SVG pitch presents the observed state alongside a non-mutating alternative, with progressive layers for candidate geometry, direct lanes, third-player routes, and tactical score components. The evidence drawer exposes hashes, versions, lifecycle state, replay outcome, and claim verification status.

The browser maps returned coordinates to pixels and normalizes server-returned pressure values for display only. It never calculates trusted geometry, opportunity, interaction, or verification results. See `docs/INVESTIGATION_WORKSPACE.md` for UI states, accessibility behavior, and the frontend trust boundary.

## Grounded explanation workflow

Phase 5 adds provider-neutral Analyst, Narrator, and Editorial Verifier boundaries. The Analyst retrieves registered calculations and verified claims without deriving new tactical values. The Narrator emits only `INTERPRETATION` sentences with sentence-level citations. The deterministic Editorial Verifier independently replays source claims, checks every number and unit, rejects unsupported probability/xT/causal language, and alone assigns publication status.

The default `local-template-v0.1` provider is deterministic and requires no network access. Microsoft Foundry was not connected because the repository has no configured Foundry project endpoint or model deployment and the relevant implementation skills are unavailable. See `docs/EXPLANATIONS.md` for contracts, lifecycle rules, and provider status.

## Evidence trust boundary

Phase 3 records canonical inputs, outputs, model/configuration versions, SHA-256 hashes, dependency links, and claim decisions. Calculation IDs use `calc:<kind>:<20-character-hash>`. A changed dependency becomes `STALE`; explicitly untrustworthy evidence becomes `INVALIDATED`. These lifecycle states remain separate from the claim outcomes `SUPPORTED`, `QUALIFIED`, `REJECTED`, and `STALE`.

The authority chain is football state → deterministic calculation → evidence artifact → verified claim → AI explanation → publication. Generated prose cannot verify itself. See `docs/VERIFICATION.md` for the complete rules and replay contract.

## Repository map

- `apps/api`: FastAPI application, deterministic tactical primitives, and evidence engine.
- `apps/api/app/explanations`: grounded explanation roles, provider boundary, registry, and editorial verifier.
- `apps/web`: React/TypeScript visual investigation workspace and component tests.
- `data/fixtures`: deterministic synthetic football states.
- `docs`: product, architecture, mathematics, contracts, verification, demo, and skill records.
- `.agents/skills`: project-local HANGO domain skills.
- `infra/azure`: reserved for a later Azure phase; empty by design.
