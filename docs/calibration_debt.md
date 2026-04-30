# Calibration Debt Log

Like a security debt log, this file tracks strata where CONCLAVE's calibration is
known to be unreliable or under-sampled.

## Open Items

| ID | Stratum | Issue | Severity | Opened |
|----|---------|-------|----------|--------|
| CD-001 | Non-European ancestries (gnomAD) | PM2 AF thresholds calibrated primarily on European data | High | 2024-01-01 |
| CD-002 | Mitochondrial variants | mtDNA heteroplasmy not handled by standard ACMG rules | High | 2024-01-01 |
| CD-003 | Somatic variants | CONCLAVE designed for germline only | Medium | 2024-01-01 |
| CD-004 | Structural variants | Criterion agents only handle SNVs and small indels | Medium | 2024-01-01 |
| CD-005 | Splicing variants | SpliceAI integration incomplete | Medium | 2024-01-01 |
| CD-006 | VUS-conflicting records | ClinVar conflicts not fully resolved | Low | 2024-01-01 |

## Resolved Items
_None yet._
