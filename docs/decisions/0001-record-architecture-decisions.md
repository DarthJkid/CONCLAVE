# 0001 — Record architecture decisions

**Status:** Accepted
**Date:** 2026-04-30

## Context

CONCLAVE is intended to be a research-grade clinical-genomics platform with a target
publication venue (ML4H) and an explicit reliability posture.
Architectural choices made implicitly in week 1 will
become invisible by week 5 and uninspectable by week 8. The cost of
recording each choice is roughly five minutes; the cost of not recording
it is hours of confusion later, plus a paper that cannot be reviewed
because the rationale is missing.

## Decision

We will record every architecturally significant decision as an ADR in
`docs/decisions/`, numbered sequentially, using the format below.

Each ADR has four sections: **Context** (the problem and constraints),
**Decision** (what we chose), **Consequences** (what becomes easier
or harder), and **Alternatives considered** (what we rejected and why).

ADRs are immutable once accepted. To change a decision, write a new ADR
that supersedes the old one and update the old one's status to
"Superseded by 000N".

## Consequences

- Future contributors can reconstruct the reasoning behind any major choice.
- The paper's reproducibility section can cite ADRs directly.
- A small ongoing time cost (~5 min per significant decision).


## Alternatives considered

- **No formal record.** Rejected: It does not survive scrutiny.
- **Issue-tracker comments.** Rejected: They are not
  version-controlled with the code and are easy to lose.
- **In-line code comments only.** Rejected: Architectural
  rationale is cross-cutting and does not live in any single file.
