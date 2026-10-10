# HANGO

HANGO reveals and verifies the hidden relational geometry behind decisive football moments.

This Phase 0/1/2 repository provides an offline-first monorepo foundation, validated data contracts, synthetic fixtures, a deterministic tactical engine, typed FastAPI endpoints, and a minimal Vite/React boot screen. It deliberately does not implement a calibrated xT model, full pitch control, Foundry agents, or Azure deployment.

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
- `POST /api/tactical/interaction`

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

## Repository map

- `apps/api`: FastAPI application and deterministic tactical primitives.
- `apps/web`: minimal React/TypeScript boot screen.
- `data/fixtures`: deterministic synthetic football states.
- `docs`: product, architecture, mathematics, contracts, verification, demo, and skill records.
- `.agents/skills`: project-local HANGO domain skills.
- `infra/azure`: reserved for a later Azure phase; empty by design.
