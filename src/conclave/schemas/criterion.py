"""CriterionInput, CriterionOutput, and Strength Pydantic models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from conclave.schemas.evidence import EvidenceBundle
from conclave.schemas.variant import Variant


class Strength(StrEnum):
    """ACMG/AMP evidence strength levels."""

    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    SUPPORTING = "supporting"
    STAND_ALONE = "stand_alone"


class Direction(StrEnum):
    PATHOGENIC = "pathogenic"
    BENIGN = "benign"
    UNCERTAIN = "uncertain"


class CriterionInput(BaseModel):
    """Input to a criterion agent."""

    variant: Variant
    criterion: str = Field(..., description="ACMG/AMP criterion code, e.g. PM2")
    evidence_bundle: EvidenceBundle | None = None
    context: dict = Field(default_factory=dict, description="Extra context for the agent")


class CriterionOutput(BaseModel):
    """Structured output from a criterion agent."""

    criterion: str
    met: bool = Field(..., description="Whether the criterion is met")
    strength: Strength | None = Field(
        None,
        description="Evidence strength when criterion is met; None when unmet",
    )
    direction: Direction | None = Field(
        None,
        description="Pathogenic or benign direction when criterion is met",
    )
    rationale: str = Field(..., description="Free-text explanation of the decision")
    evidence_bundle: EvidenceBundle | None = None
    abstain: bool = Field(
        False,
        description="True when the agent cannot make a reliable determination",
    )
    abstention_reason: str | None = Field(
        None,
        description="Reason for abstention when abstain=True",
    )
    raw_llm_output: str | None = Field(
        None,
        description="The verbatim LLM output used to derive this result (for audit)",
    )
