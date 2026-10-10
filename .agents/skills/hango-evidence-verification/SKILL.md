---
name: hango-evidence-verification
description: Design or review HANGO evidence references, tactical claim verification, publication status, version checks, and correction or invalidation behavior. Use when implementing the evidence layer, lie detector, verified narrative workflow, or claim audit; never let generated prose self-verify.
---

# HANGO Evidence Verification

## Keep evidence traceable

Require each evidence reference to identify its stable ID, evidence kind, event or snapshot ID, calculation ID when applicable, model version, source/provenance, and validity state. Make every factual number traceable to deterministic inputs and a reproducible calculation.

Keep `OBSERVED`, `CALCULATED`, `MODEL_ESTIMATE`, and `INTERPRETATION` distinct in storage and presentation.

## Verify before publication

1. Confirm every referenced event, snapshot, calculation, and model version exists.
2. Recompute or integrity-check deterministic numerical values.
3. Confirm the claim's classification matches its evidence.
4. Reject or qualify unsupported tactical intent, causal, or certainty claims.
5. Assign exactly one publication status.

Use these statuses:

- `SUPPORTED`: current evidence fully supports the factual wording.
- `QUALIFIED`: only narrower or explicitly interpretive wording is supportable.
- `REJECTED`: evidence is absent, contradictory, or the claim overreaches.
- `STALE`: referenced input, calculation, or model version is no longer current.

## Separate roles

Do not allow model prose to approve itself. A verifier must operate from source records and deterministic outputs rather than trusting a narrator's embedded numbers or citations.

## Correct and invalidate

Preserve audit history. Create a new version when correcting evidence, mark superseded evidence invalid or stale, and transitively mark dependent claims stale. Never silently rewrite a published factual record. Reverification may issue a new status after the corrected evidence passes all checks.
