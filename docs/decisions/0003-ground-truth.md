# ADR 0003: Ground Truth — ClinVar Expert Panel Reviews

**Status:** Accepted
**Date:** 2024-01-01

## Context
We need a gold-standard dataset to evaluate CONCLAVE's classification accuracy.

## Decision
Use **ClinVar variants reviewed by Expert Panels** (review status ≥ 3 stars) as ground truth. These represent the highest-confidence community-reviewed classifications.

## Consequences
- Expert Panel reviews represent the best available community consensus.
- Dataset is limited to variants with sufficient review activity.
- Potential circular reasoning if ClinVar data is also used as evidence input — must be handled carefully.
