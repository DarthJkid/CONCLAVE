"""PathogenicityVerdict and CalibratedVerdict Pydantic models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from conclave.schemas.criterion import CriterionOutput


class ACMGClassification(StrEnum):
    PATHOGENIC = "Pathogenic"
    LIKELY_PATHOGENIC = "Likely_pathogenic"
    UNCERTAIN_SIGNIFICANCE = "Uncertain_significance"
    LIKELY_BENIGN = "Likely_benign"
    BENIGN = "Benign"


class PathogenicityVerdict(BaseModel):
    """ACMG/AMP-aligned pathogenicity verdict for a variant."""

    variant_id: str
    classification: ACMGClassification
    criterion_outputs: list[CriterionOutput] = Field(default_factory=list)
    rationale: str = Field(..., description="Aggregated rationale across all criteria")
    met_criteria: list[str] = Field(default_factory=list, description="Codes of criteria that were met")
    abstained_criteria: list[str] = Field(
        default_factory=list,
        description="Codes of criteria where the agent abstained",
    )


class CalibratedVerdict(BaseModel):
    """Verdict after conformal calibration — may include abstention."""

    verdict: PathogenicityVerdict
    posterior_pathogenic: float = Field(
        ..., ge=0.0, le=1.0, description="Posterior probability of pathogenicity"
    )
    prediction_set: list[ACMGClassification] = Field(
        ...,
        description="Conformal prediction set: all classes not excluded at the target error rate",
    )
    target_error_rate: float = Field(
        0.1, ge=0.0, le=1.0, description="Desired marginal coverage error rate (1 - coverage)"
    )
    abstain: bool = Field(
        False,
        description="True when the prediction set contains >1 class at the target error rate",
    )
    calibration_note: str | None = None
