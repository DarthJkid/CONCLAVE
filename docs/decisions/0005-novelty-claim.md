# ADR 0005: Novelty Claim

**Status:** Accepted
**Date:** 2026-04-30

## Context
Several existing tools (InterVar, AutoACMG, VarSome) perform ACMG/AMP-aligned variant classification. We need to articulate CONCLAVE's distinct contribution.

## Decision
CONCLAVE's novelty claims are:
1. **Per-criterion LLM agents with conformal abstention** — agents say "I don't know" at a calibrated error rate.
2. **Full evidence provenance** — every decision includes a hash-verified audit trail.
3. **Modular criterion architecture** — each ACMG/AMP criterion is a separate replaceable agent.
4. **Calibrated uncertainty** — outputs include prediction sets, not just point classifications.

## Consequences
- Evaluation must demonstrate that abstention is better-calibrated than existing tools.
- Provenance hashing adds latency; mitigated by async I/O.
