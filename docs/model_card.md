# CONCLAVE Model Card

## Model Details
- **Name:** CONCLAVE
- **Version:** 0.1.0
- **Type:** Multi-agent LLM orchestration system for genomic variant interpretation

## Intended Use
- **Primary use:** Research and clinical decision support for ACMG/AMP-aligned variant classification.
- **Users:** Clinical geneticists, genomics researchers, bioinformaticians.
- **Out-of-scope:** Not intended as a standalone clinical diagnostic tool without human expert review.

## Factors
- Gene-disease context heavily influences criterion applicability.
- Population ancestry affects allele frequency thresholds (PM2).

## Metrics
- Sensitivity and specificity vs. ClinVar Expert Panel reviews (see `reports/metrics/`).
- Abstention rate as a function of uncertainty.

## Evaluation Data
- ClinVar Expert Panel variants (≥3 stars) — see `docs/datasheet.md`.

## Ethical Considerations
- Misclassification of variants can have serious clinical consequences.
- CONCLAVE includes conformal abstention to flag uncertain cases.
- All outputs should be reviewed by a qualified human expert.

## Caveats and Recommendations
- Performance may degrade for genes/variants under-represented in training data.
- See `docs/calibration_debt.md` for known under-sampled strata.
