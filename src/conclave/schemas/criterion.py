"""Criterion schemas: input and output contract for every criterion agent.

The `Criterion` enum names the 28 ACMG/AMP criteria from Richards et al.
2015. The `CriterionOutput` schema is the contract that every one of the
28 criterion agents must satisfy.

A criterion's outcome is one of three states:
- fired (fired=True): evidence supports invoking this criterion
- did not fire (fired=False): evidence does not support this criterion
- abstained (fired=None): the agent declines to decide, usually because
  evidence is insufficient. This is the conformal-abstention output.

When abstained, strength must be None and abstention_reason must be set.
When fired (True or False), strength may or may not be set depending on
the criterion's specification.

See ADR-0006 (schema spine) and the project spec, sections 5.3 and 7.2.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from conclave.schemas.evidence import EvidenceBundle
from conclave.schemas.variant import GeneContext, Variant


class Criterion(StrEnum):
    """The 28 ACMG/AMP criteria from Richards et al. 2015.
    Pathogenic-direction criteria: PVS1, PS1-4, PM1-6, PP1-5
    Benign-direction criteria: BA1, BS1-4, BP1-7
    """

    # Pathogenic - Very Strong
    PVS1 = "PVS1"

    # Pathogenic - Strong
    PS1 = "PS1"
    PS2 = "PS2"
    PS3 = "PS3"
    PS4 = "PS4"

    # Pathogenic - Moderate
    PM1 = "PM1"
    PM2 = "PM2"
    PM3 = "PM3"
    PM4 = "PM4"
    PM5 = "PM5"
    PM6 = "PM6"

    # Pathogenic - Supporting
    PP1 = "PP1"
    PP2 = "PP2"
    PP3 = "PP3"
    PP4 = "PP4"
    PP5 = "PP5"

    # Benign - Stand Alone
    BA1 = "BA1"

    # Benign - Strong
    BS1 = "BS1"
    BS2 = "BS2"
    BS3 = "BS3"
    BS4 = "BS4"

    # Benign - Supporting
    BP1 = "BP1"
    BP2 = "BP2"
    BP3 = "BP3"
    BP4 = "BP4"
    BP5 = "BP5"
    BP6 = "BP6"
    BP7 = "BP7"


class Strength(StrEnum):
    """ACMG strength weighting (Tavtigian 2018 point system)

    The integer values that map to these are defined in the aggregator,
    not here, strength is just a qualitative label. Not a number.
    """

    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    SUPPORTING = "supporting"


class CriterionInput(BaseModel):
    """The input passed to the criterion agent.

    Agents do not modify these objects; they read them and produce a
    CriterionOutput. The orchestrator is responsible for assembling the input.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    variant: Variant = Field(
        ...,
        description="The genetic variant being evaluated.",
    )

    gene_context: GeneContext = Field(
        ...,
        description="Gene-level context for the variant. Note: this duplicates "
        "variant.gene; we keep it here because some agents need richer "
        "gene-context data (haploinsufficiency, dosage sensitivity, etc.)  "
        "that the variant resolver populates.",
    )

    evidence_bundle: EvidenceBundle = Field(
        ..., description="Pre-assembled evidence bundle this agent will reason over."
    )


class CriterionOutput(BaseModel):
    """
    Output produced by a criterion agent.

    Three possible states (see module docstring):
    - fired=True, strength=<some>: criterion is invoked at this strength
    - fired=False, strength=None: criterion does not apply.
    - fired=None, abstained=True, abstention_reason=<text>: agent declines.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    criterion: Criterion = Field(..., description="Which of the 28 criteria this is.")

    fired: bool | None = Field(
        ...,
        description="True/False if the agent decided; None if abstained.",
    )

    strength: Strength | None = Field(
        ...,
        description="Strength level when fired=True; None otherwise.",
    )

    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ...,
        description=(
            "Pre-calibrated confidence score in the correctness of this output, between 0 and 1. "
            "uses this to decide abstenstion thresholds."
        ),
    )

    abstained: bool = Field(
        ...,
        description="True if fired is None (redundant flag for clarity in JSON).",
    )

    abstention_reason: Annotated[str, StringConstraints(max_length=500)] | None = Field(
        None,
        description="Required when abstained=True; None otherwise.",
    )

    evidence: EvidenceBundle = Field(
        ...,
        description="Evidence bundle the agent considered (echoed for audit).",
    )

    reasoning: Annotated[str, StringConstraints(max_length=5000)] = Field(
        ...,
        description="Short structured reasoning from the agent justifying its decision.",
    )

    @model_validator(mode="after")
    def state_must_be_consistent(self) -> CriterionOutput:
        """Enforce the three-state invariant.

        - If fired is None: abstained must be True, abstention_reason must
        be a non-empty string, strength must be None.
        - If fired is True or False: abstained must be False, abstention_reason
        must be None.
        - If fired is True: strength must not be None.
        - If fired is False: strength must be None.

        """

        if self.fired is None:
            if not self.abstained:
                raise ValueError("fired=None requires abstained=True")
            if self.abstention_reason is None or len(self.abstention_reason.strip()) == 0:
                raise ValueError("Abstained outputs must include a non-empty abstention_reason")
            if self.strength is not None:
                raise ValueError("Abstained outputs must have strength=None.")
        else:
            if self.abstained:
                raise ValueError("fired is decided; abstained must be False.")
            if self.abstention_reason is not None:
                raise ValueError("Decided outputs must have abstention_reason=None.")
            if self.fired is True and self.strength is None:
                raise ValueError("fired=True requires strength to be set.")
            if self.fired is False and self.strength is not None:
                raise ValueError("fired=False requires strength=None.")
        return self
