# ADR 0004: Determinism Contract

**Status:** Accepted
**Date:** 2026-04-30

## Context
Reproducibility is a first-class requirement for clinical tools. LLM outputs are stochastic by default.

## Decision
CONCLAVE enforces a **determinism contract**: given the same input variant, the same model snapshot, and `temperature=0.0`, the pipeline must produce byte-for-byte identical `AuditTrail.compute_fingerprint()` values.

CI gate: `tests/determinism/` runs the full pipeline twice on each golden variant and asserts fingerprint equality.

## Consequences
- All LLM calls must use `temperature=0.0`.
- Model version pins (snapshots) are mandatory in `conf/models/`.
- Non-deterministic components (e.g. timestamp fields) are excluded from the fingerprint.
