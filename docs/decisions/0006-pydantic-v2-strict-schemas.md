# 0006 - Pydantic v2 with strict frozen schemas as a spine

**Status:** Accepted
**Date:** 2026-04-30

## Context

CONCLAVE has approximately fifteen distinct data contracts (Variant, Evidence, CriterionInput, CriterionOutput, PathogenicityVeridct, ...).
These are consumed by:

1. The Criterion agents (every agent reads CriterionInput and writes CriterionOutput).
2. The FastAPI HTTP surface (request/response models).
3. The LLM structured-output system (the agent's output JSON schema is used as a prompt constraint).
4. The Streamlit UI (renders structured outputs).
5. Tests (golden fixtures, property-based generators).
6. The published model card and paper appendix (documents the schemas).

If any of these consumers describes a contract independently, the
contracts will drift. The drift is the leading cause of "everything
mysteriously broke" reports in ML systems (Sculley et al. 2015).

## Decision

We will:

1. Define every data contract as a Pydantic v2 `BaseModel` in
   `src/conclave/schemas/`.
2. Configure every model with `frozen=True` (immutable),
   `extra="forbid"` (reject unknown fields), and `str_strip_whitespace=True`.
3. Use `Annotated` types with `StringConstraints` and `Field` constraints
   for declarative validation that is visible in the JSON schema.
4. Use `field_validator` only for cross-field invariants that cannot be
   expressed declaratively.
5. Generate everything else (FastAPI types, LLM schemas, JSON schemas
   for documentation) from these models — never duplicate.

## Consequences

- A schema change is a single-file change. CI surfaces all downstream
  effects.
- LLM hallucination of out-of-schema fields is impossible (rejected at
  validation).
- Developer tax: every new field requires writing the validator and the
  test.
- Pydantic v2 has a non-trivial learning curve compared to v1. We accept
  this cost for the performance and the strict-by-default behaviour.

## Alternatives considered

- **`dataclasses` with `__post_init__` validators.** (Stdlib, no
  dependency)
  Rejected: no built-in JSON schema generation,
  no built-in JSON serialisation, no built-in immutability.
- **`attrs` with validators.** Mature, lightweight.
    Rejected: the rest of the ecosystem (FastAPI, instructor for structured LLM output) assumes Pydantic.
- **Pydantic v1.**
    Rejected: Stable but in maintenance mode and slower.
