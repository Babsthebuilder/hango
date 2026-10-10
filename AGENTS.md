# HANGO Engineering Constitution

## Mission

Build HANGO as an evidence-backed football relational intelligence and broadcast storytelling product.

## Non-negotiable architecture

- Keep tactical mathematics deterministic and runnable without Azure.
- Never use AI to calculate geometry or create trusted tactical metrics.
- Never allow AI-generated prose to approve or verify itself.
- Treat Microsoft Foundry as a later explanation and orchestration layer.
- Keep observations, deterministic calculations, model estimates, and interpretations distinct.
- Do not introduce unnecessary microservices, a full-match simulator, 3D replay, Match DNA, or speculative features.

## Code quality

- Type every public Python interface.
- Validate external boundaries with Pydantic v2.
- Make thresholds configurable and mathematical model versions explicit.
- Add tests alongside implementation and use deterministic fixtures.
- Fail loudly on invalid football state.

## Scope rule

Do not add a feature because it sounds impressive. Every addition must improve at least one of:

1. tactical correctness;
2. explainability;
3. verification;
4. judge-facing UX;
5. Microsoft challenge alignment.

## Skill activation

Load at most two or three relevant skills for an implementation task unless a clear need is documented. HANGO project skills live in `.agents/skills/`.

- Data contracts: `pydantic-models-py` and `hango-synthetic-fixtures` when available.
- Backend API: `fastapi-router-py` and `pydantic-models-py` when available.
- Tactical mathematics: `hango-football-geometry` only; do not load Azure or frontend skills.
- Evidence: `hango-evidence-verification` and `pydantic-models-py` when available.
- Frontend: `frontend-ui-dark-ts`, `zustand-store-ts`, and `hango-studio-design` when the interactive frontend starts.
- Foundry: defer Azure skills until the local engine works and Azure resources exist.
