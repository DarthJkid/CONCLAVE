# 0007 — Pin development tool versions exactly

Date: 2026-04-30
Status: Accepted

## Context

CI run #1 (commit f2029b6) failed in the lint job because the CI runner
installed ruff 0.15.12 while the local Codespace had an older ruff that
treated the `tests/unit/schemas/test_variant.py` import block as
correctly sorted. Newer ruff applied a stricter import-organization rule
(I001) and rejected the same code that the local environment accepted.

i.e Version drift: identical source code producing different
verdicts in different environments because the toolchain itself moved.

## Decision

All development tool versions in `[project.optional-dependencies] dev`
are pinned with `==` constraints rather than `>=`. The pinned versions
match those installed in the failing CI run, since CI is the canonical
environment for the project.

The lock file `uv.lock` continues to record full transitive pins.

To update a tool, the procedure is:

1. Update the `==` constraint in `pyproject.toml`.
2. Run `uv sync --all-extras`.
3. Run the full local CI loop (`ruff check`, `ruff format --check`,
   `mypy`, `pytest`).
4. Fix any new violations introduced by the updated tool.
5. Commit the change with a message of the form
   `chore(deps): bump <tool> from X.Y.Z to A.B.C` and reference any
   newly enforced rules.

Proposed cadence: quarterly review of all dev tool versions. A new ADR
records each major upgrade (ruff 0.x → 1.0, mypy major version, etc.).

## Consequences

- CI and local environments produce identical lint/type verdicts.
- Tool updates become deliberate events, not silent ones.
- The project will fall behind on new features/fixes between updates.
  Accepted as the cost of reproducibility.
- Production runtime dependencies (Pydantic) remain on `>=,<` ranges
  for now — this ADR covers only the dev tooling. A future ADR will
  decide policy on runtime pins (likely also exact, post-week-2).

## Alternatives considered

- **Keep `>=` constraints, accept occasional CI failures.** Rejected:
  it shifts debugging time from the rare update event to every CI run.
- **Pin only ruff and mypy.** Rejected: incomplete; leaves pytest and
  hypothesis as silent drift sources.
- **Use Renovate or Dependabot for automated updates.** Defer: useful
  but adds another moving part. Revisit once the project has one or
  two paid maintainers, which is not now.
