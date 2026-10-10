# Skill Inventory

Catalog checked on 2026-10-10 with `npx skills add microsoft/skills --list`. The catalog HEAD was `d5741a1e9325adead3a28d1d203bb69283907e06`. Project-local skills use `.agents/skills/`, the discovery path used by the installed agent-skill system. No requested Microsoft skill was duplicated or silently substituted.

| Skill | Source | Installed | Phase | Use |
|---|---|---:|---|---|
| `fastapi-router-py` | `microsoft/skills` | No — unavailable in current catalog | Backend | Use for FastAPI routing and typed responses; never define tactical mathematics with it. |
| `pydantic-models-py` | `microsoft/skills` | No — unavailable in current catalog | Data contracts | Use for Pydantic v2 boundary contracts; do not use as the tactical calculation engine. |
| `frontend-ui-dark-ts` | `microsoft/skills` | No — unavailable in current catalog | Interactive UI | Use for the later premium dark interface; not for Phase 1 mathematics or repository architecture. |
| `zustand-store-ts` | `microsoft/skills` | No — unavailable in current catalog | Interactive UI | Introduce only when interactive frontend state begins. |
| `azure-ai-projects-py` | `microsoft/skills` | No — unavailable in current catalog | Foundry | Use only after an Azure tenant/project exists and the local tactical core works. |
| `agent-framework-azure-ai-py` | `microsoft/skills` | No — unavailable in current catalog | Foundry agents | Use for later Analyst/Narrator/Verifier orchestration; never for tactical calculations. |
| `azure-identity-py` | `microsoft/skills` | No — unavailable in current catalog | Azure auth | Use for Entra/managed identity later; never hardcode secrets. |
| `azure-monitor-opentelemetry-py` | `microsoft/skills` | No — unavailable in current catalog | Stabilization | Use for deployed tracing and monitoring, not the offline core. |
| `azure-microsoft-playwright-testing-ts` | `microsoft/skills` | No — unavailable in current catalog | E2E | Use late for the judge journey; local Playwright comes first. |
| `skill-creator` | Codex system skill (`C:/Users/USER/.codex/skills/.system/skill-creator`) | Yes — preinstalled, not duplicated | Phase 0/1 | Use to create and validate focused local skills; not as a domain substitute. |
| `hango-football-geometry` | Project-local | Yes — `.agents/skills/hango-football-geometry` | Tactical mathematics | Use for deterministic geometry, lanes, pressure specifications, and interaction algebra; no Azure/frontend work. |
| `hango-evidence-verification` | Project-local | Yes — `.agents/skills/hango-evidence-verification` | Evidence | Use for claim/evidence verification and invalidation; prose cannot self-verify. |
| `hango-synthetic-fixtures` | Project-local | Yes — `.agents/skills/hango-synthetic-fixtures` | Data/testing | Use to create valid deterministic football fixtures without embedding expected answers. |
| `hango-studio-design` | Project-local | Yes — `.agents/skills/hango-studio-design` | UI | Use only during UI/studio implementation for HANGO's broadcast visual principles. |

## Version and provenance

The live Microsoft catalog was cloned by `skills` CLI 1.7.2 from `https://github.com/microsoft/skills.git`; its discoverable HEAD was `d5741a1e9325adead3a28d1d203bb69283907e06`. Because none of the requested, not-already-installed names were present, no Microsoft repository files were installed and no lock entry was created. Local HANGO skills are repository-versioned with this project; their installation paths are the `.agents/skills/<skill-name>` paths shown in the table. The preinstalled system `skill-creator` did not expose a package version in its metadata.
