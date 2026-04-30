# CONCLAVE

**Calibrated Orchestrated Network of Criterion-level LLM Agents for Variant Evaluation**

Multi-agent ACMG/AMP variant interpretation with per-criterion conformal abstention,
stratified calibration against ClinGen Variant Curation Expert Panels, and
citation-faithfulness verification.

> **Status: pre-alpha.** This is a research & personal portfolio project. I am not a Geneticist, nor do I have any qualification in genomics or the wider biomedical science. Do not use the outputs for
> direct clinical decision-making. See `docs/system_card.md` for intended use
> and limitations.

## Quick start

```bash
git clone git@github.com:yourname/conclave.git
cd conclave
uv sync --all-extras
uv run pytest
```

## Documentation

- [Project specification](docs/spec.md)
- [Architecture decision records](docs/decisions/)
- [Model card](docs/model_card.md)
- [System card](docs/system_card.md)
- [Dataset datasheet](docs/datasheet.md)
- [Reproducibility instructions](docs/reproducibility.md)
- [Calibration debt log](docs/calibration_debt.md)

## Citing

If you use CONCLAVE in research, please cite via the metadata in `CITATION.cff`.

## License

MIT — see [LICENSE](LICENSE).
