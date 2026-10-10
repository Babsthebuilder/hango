# Grounded explanations and editorial verification

Phase 5 implements the next link in HANGO's trust chain without granting generative prose authority over football truth.

```text
registered calculation + verified claim
                 |
                 v
          read-only Analyst
                 |
                 v
       provider-backed Narrator
        (INTERPRETATION only)
                 |
                 v
 deterministic Editorial Verifier
                 |
          READY or BLOCKED
```

## Role boundaries

The Analyst retrieves immutable calculation artifacts and claim records by stable ID. It has no tactical engine dependency and performs no geometry, pressure, opportunity, or interaction calculation.

The Narrator receives only this grounding packet. A provider returns sentences and citations. It cannot set lifecycle, verification status, or publication readiness. All drafts are `INTERPRETATION`.

The Editorial Verifier distrusts the draft. It re-verifies source claims, replays their calculations through the existing evidence engine, validates citation paths/units/values, checks displayed numeric rounding, checks source lifecycle, and applies deterministic language restrictions.

## Provider abstraction

`ExplanationProvider.compose` is the replaceable provider boundary. `local-template-v0.1` is the only configured provider in Phase 5. It deterministically restates registered claims and copies their authoritative numerical assertions into sentence citations. Tests can inject fixed or failing providers without network access.

A later Foundry adapter must implement this same interface. It may compose language but cannot calculate values, write evidence, or return an editorial decision.

## Lifecycle and publication

Explanation validity (`VALID`, `STALE`, `INVALIDATED`), editorial decision (`SUPPORTED`, `QUALIFIED`, `REJECTED`, `STALE`), and publication state (`DRAFT`, `READY`, `BLOCKED`, `STALE`, `INVALIDATED`) are separate fields.

`READY` means the deterministic gate permits an editor to publish. It is not autonomous publication. `QUALIFIED` is ready only because its upstream qualification is explicit and retained. Retrieval refreshes the decision against current evidence. Explicit invalidation is append-only and never deletes the earlier decision.

## Foundry status

Azure CLI authentication is active, but Phase 5 found no configured `AZURE_AI_PROJECT_ENDPOINT` or `AZURE_AI_MODEL_DEPLOYMENT_NAME`, and no installed Foundry/Agent Framework/Azure Identity implementation skill. No Azure dependency, endpoint, credential, or speculative adapter was added.

A future integration requires an existing Foundry project endpoint, a deployed model name, the relevant current skills/SDK guidance, and an authenticated identity with access to that project. Secrets must not be committed or printed.
