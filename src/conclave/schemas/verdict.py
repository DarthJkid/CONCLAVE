"""Verdict schemas.

After the aggregator combines the criterion outputs, it produces a
PathogenicityVerdict with:
- A five-tier label (Pathogenic, Likely Pathogenic, VUS, Likely Benign, Benign).
- The Tavtigian point total that led to that label.
- The criterion outputs that fired (with their strengths and confidences).
- The criterion outputs that abstained (with their abstention reasons).

After the verdict-level conformal calibrator runs, we wrap the verdict
in a CalibratedVerdict that adds:
- The conformal alpha used and the empirical coverage at that alpha.
- The calibrator version (since calibration evolves as more VCEP data arrives).
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from conclave.schemas.criterion import CriterionOutput


class PathogenicityTier(StrEnum):
    """The five-tier ACMG pathogenicity classification."""

    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    VUS = "vus"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"


class PathogenicityVerdict(BaseModel):
    """The aggregator's verdict on a variant.

    The `tier` is determined by the aggregator, which applies the
    Tavtigian point system. The score and tier may not have a 1:1
    mapping when criteria conflict — the aggregator's combination
    rules decide.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    tier: PathogenicityTier = Field(
        ...,
        description="The five-tier pathogenicity label.",
    )
    tavtigian_score: Annotated[float, Field(ge=-50.0, le=50.0)] = Field(
        ...,
        description="The Tavtigian point total computed from the fired criteria.",
    )
    fired_criteria: tuple[CriterionOutput, ...] = Field(
        ...,
        description="The criterion outputs that fired (each has fired=True).",
    )
    abstained_criteria: tuple[CriterionOutput, ...] = Field(
        ...,
        description="The criterion outputs that abstained (each has fired=None).",
    )
    reasoning_summary: Annotated[str, StringConstraints(max_length=1000)] = Field(
        ...,
        description=("Concise, human-readable summary of the reasoning that led to this verdict."),
    )

    @model_validator(mode="after")
    def check_criteria_consistency(self) -> PathogenicityVerdict:
        """Three invariants on the criterion lists.

        1. Every entry in fired_criteria has fired=True.
        2. Every entry in abstained_criteria has fired=None and abstained=True.
        3. No criterion appears in both lists (disjoint sets).
        """
        for output in self.fired_criteria:
            if output.fired is not True:
                raise ValueError(
                    f"fired_criteria contains an entry with fired={output.fired} "
                    f"for criterion {output.criterion}. Expected fired=True."
                )

        for output in self.abstained_criteria:
            if not output.abstained:
                raise ValueError(
                    f"abstained_criteria contains a non-abstained entry "
                    f"for criterion {output.criterion}."
                )

        fired_names = {c.criterion for c in self.fired_criteria}
        abstained_names = {c.criterion for c in self.abstained_criteria}
        overlap = fired_names & abstained_names
        if overlap:
            raise ValueError(f"A criterion cannot be both fired and abstained. Overlap: {overlap}")

        return self


class CalibratedVerdict(BaseModel):
    """A PathogenicityVerdict wrapped with verdict-level calibration metadata.

    Reports an honest empirical coverage, which is allowed to diverge
    from the nominal (1 - alpha). Divergence is itself a research-grade
    finding; the schema does not silently reject it.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    verdict: PathogenicityVerdict = Field(
        ...,
        description="The uncalibrated pathogenicity verdict.",
    )
    conformal_alpha: Annotated[float, Field(gt=0.0, lt=1.0)] = Field(
        ...,
        description="The miscoverage level alpha used during calibration.",
    )
    conformal_coverage: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ...,
        description=(
            "The empirical coverage observed on the held-out calibration set "
            "at this alpha. Allowed to diverge from the nominal 1-alpha."
        ),
    )
    calibrator_version: Annotated[
        str, StringConstraints(pattern=r"^[A-Za-z0-9._-]+$", min_length=1, max_length=50)
    ] = Field(
        ...,
        description="Version tag of the calibrator (e.g. 'calibrator-v2-stratified-2026-04').",
    )
    calibrated_at: datetime = Field(
        ...,
        description="UTC timestamp when calibration was applied.",
    )

    @field_validator("calibrated_at")
    @classmethod
    def must_be_timezone_aware_utc(cls, value: datetime) -> datetime:
        """Same UTC-only rule as Provenance.retrieval_timestamp."""
        if value.tzinfo is None:
            raise ValueError("calibrated_at must be timezone-aware (UTC).")
        if value.tzinfo != UTC:
            return value.astimezone(UTC)
        return value
