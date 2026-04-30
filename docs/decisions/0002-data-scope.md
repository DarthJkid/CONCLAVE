# ADR 0002: Data Scope — gnomAD, ClinVar, PubMed Only

**Status:** Accepted
**Date:** 2024-01-01

## Context
CONCLAVE requires population frequency, clinical significance, and literature data. Many databases are available (gnomAD, ExAC, 1000G, ClinVar, HGMD, LOVD, PubMed, etc.).

## Decision
Initially scope data retrieval to **gnomAD v4**, **ClinVar**, and **PubMed** via their public APIs. HGMD and LOVD require institutional licenses.

## Consequences
- All data sources are freely accessible (no license procurement required).
- gnomAD v4 has the largest allele frequency data available.
- HGMD variants will be missed; this is flagged in `docs/calibration_debt.md`.
