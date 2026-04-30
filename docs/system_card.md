# CONCLAVE System Card

## System Overview
CONCLAVE is a multi-agent AI system for ACMG/AMP-aligned genomic variant interpretation. It orchestrates 28 criterion-level LLM agents, each responsible for evaluating one ACMG/AMP evidence criterion.

## Components
| Component | Description |
|-----------|-------------|
| Criterion Agents | One per ACMG/AMP criterion; produces structured `CriterionOutput` |
| Orchestrator | FastAPI app dispatching agents in parallel via asyncio |
| Calibration Layer | Conformal prediction set construction |
| Aggregator | Tavtigian + Richards verdict combination |
| Verifier | NLI-based citation faithfulness checker |
| Retrieval | gnomAD, ClinVar, PubMed adapters |
| CLI | `conclave` command-line interface |
| UI | Streamlit dashboard |

## Deployment
- Container: `docker/Dockerfile`
- API: FastAPI on port 8000
- UI: Streamlit on port 8501

## Safety Measures
1. Conformal abstention flags uncertain cases.
2. NLI verifier rejects hallucinated citations.
3. Full audit trail with hash-verified provenance.
4. All outputs carry a human-review recommendation.
