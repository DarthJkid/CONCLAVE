# CONCLAVE Datasheet

## Datasets Used

### gnomAD v4.1
- **Purpose:** Population allele frequencies for PM2, BA1, BS1 criteria.
- **Source:** https://gnomad.broadinstitute.org
- **License:** CC0

### ClinVar (2024-05 release)
- **Purpose:** Clinical classifications for PS1, PM5 evidence; ground truth evaluation.
- **Source:** https://www.ncbi.nlm.nih.gov/clinvar/
- **License:** Public domain

### PubMed
- **Purpose:** Literature retrieval for PS3, PP1, BS3, BP2 criteria.
- **Source:** https://pubmed.ncbi.nlm.nih.gov
- **License:** Open access articles only

## Data Limitations
- gnomAD under-represents non-European ancestries; PM2 thresholds may be less reliable.
- ClinVar has known classification errors and conflicts.
- PubMed retrieval is limited to abstract-level information without full-text access.
