"""Tests for conclave.schemas.criterion."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from conclave.schemas.criterion import (
    Criterion,
    CriterionInput,
    CriterionOutput,
    Strength,
)
from conclave.schemas.evidence import (
    EvidenceBundle,
)
from conclave.schemas.variant import (
    HGVS,
    Chromosome,
    GeneContext,
    GenomicCoordinate,
    Variant,
)

# ----------------------- Fixtures -----------------------


def make_variant() -> Variant:
    return Variant(
        hgvs=HGVS(notation="NM_007294.4:c.5266dupC"),
        coordinate=GenomicCoordinate(
            chromosome=Chromosome.CHR17,
            position=43_057_062,
            reference="C",
            alternate="CC",
        ),
        gene=GeneContext(
            symbol="BRCA1",
            transcript_id="NM_007294.4",
            is_haploinsufficient=True,
        ),
    )


def make_empty_bundle() -> EvidenceBundle:
    return EvidenceBundle(
        bundle_id="test-empty",
        items=(),
        assembled_at=datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC),
    )


def make_fired_output(criterion: Criterion = Criterion.PM2) -> CriterionOutput:
    return CriterionOutput(
        criterion=criterion,
        fired=True,
        strength=Strength.MODERATE,
        confidence=0.92,
        abstained=False,
        abstention_reason=None,
        evidence=make_empty_bundle(),
        reasoning="Allele absent from gnomAD v4 (AC=0, AN>250000).",
    )


def make_abstained_output(criterion: Criterion = Criterion.PP1) -> CriterionOutput:
    return CriterionOutput(
        criterion=criterion,
        fired=None,
        strength=None,
        confidence=0.50,
        abstained=True,
        abstention_reason="No co-segregation literature found.",
        evidence=make_empty_bundle(),
        reasoning="No PubMed hits for co-segregation in BRCA1 c.5266dupC.",
    )


# ----------------------- Enum sanity -----------------------


class TestEnums:
    def test_criterion_has_28_values(self) -> None:
        assert len(list(Criterion)) == 28

    def test_strength_has_4_values(self) -> None:
        assert len(list(Strength)) == 4

    def test_criterion_round_trips_as_string(self) -> None:
        # String value of Criterion.PM2 is exactly "PM2", not "Criterion.PM2".
        assert str(Criterion.PM2) == "PM2"
        assert Criterion("PM2") == Criterion.PM2


# ----------------------- Positive paths -----------------------


class TestFiredOutput:
    def test_fired_with_strength(self) -> None:
        out = make_fired_output()
        assert out.fired is True
        assert out.strength == Strength.MODERATE
        assert out.abstained is False
        assert out.abstention_reason is None

    def test_round_trip(self) -> None:
        out = make_fired_output()
        rebuilt = CriterionOutput.model_validate_json(out.model_dump_json())
        assert rebuilt == out


class TestNotFiredOutput:
    def test_not_fired_no_strength(self) -> None:
        out = CriterionOutput(
            criterion=Criterion.BA1,
            fired=False,
            strength=None,
            confidence=0.95,
            abstained=False,
            abstention_reason=None,
            evidence=make_empty_bundle(),
            reasoning="Allele frequency 0.00001 is below 5% threshold.",
        )
        assert out.fired is False
        assert out.strength is None


class TestAbstainedOutput:
    def test_abstained_state(self) -> None:
        out = make_abstained_output()
        assert out.fired is None
        assert out.strength is None
        assert out.abstained is True
        assert out.abstention_reason is not None

    def test_abstained_round_trip(self) -> None:
        out = make_abstained_output()
        rebuilt = CriterionOutput.model_validate_json(out.model_dump_json())
        assert rebuilt == out


# ----------------------- Negative paths (the state-consistency validator) -----------------------


class TestStateConsistency:
    def test_fired_true_without_strength_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CriterionOutput(
                criterion=Criterion.PM2,
                fired=True,
                strength=None,
                confidence=0.9,
                abstained=False,
                abstention_reason=None,
                evidence=make_empty_bundle(),
                reasoning="...",
            )
        assert "strength" in str(exc_info.value).lower()

    def test_fired_false_with_strength_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CriterionOutput(
                criterion=Criterion.PM2,
                fired=False,
                strength=Strength.STRONG,  # not allowed
                confidence=0.9,
                abstained=False,
                abstention_reason=None,
                evidence=make_empty_bundle(),
                reasoning="...",
            )

    def test_abstained_with_strength_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CriterionOutput(
                criterion=Criterion.PM2,
                fired=None,
                strength=Strength.MODERATE,  # not allowed
                confidence=0.5,
                abstained=True,
                abstention_reason="ambiguous",
                evidence=make_empty_bundle(),
                reasoning="...",
            )

    def test_abstained_without_reason_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CriterionOutput(
                criterion=Criterion.PM2,
                fired=None,
                strength=None,
                confidence=0.5,
                abstained=True,
                abstention_reason=None,  # required when abstained
                evidence=make_empty_bundle(),
                reasoning="...",
            )
        assert "abstention_reason" in str(exc_info.value)

    def test_abstained_with_empty_reason_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CriterionOutput(
                criterion=Criterion.PM2,
                fired=None,
                strength=None,
                confidence=0.5,
                abstained=True,
                abstention_reason="   ",  # whitespace-only
                evidence=make_empty_bundle(),
                reasoning="...",
            )

    def test_fired_none_without_abstained_flag_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CriterionOutput(
                criterion=Criterion.PM2,
                fired=None,
                strength=None,
                confidence=0.5,
                abstained=False,  # inconsistent
                abstention_reason=None,
                evidence=make_empty_bundle(),
                reasoning="...",
            )

    def test_decided_with_abstention_reason_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CriterionOutput(
                criterion=Criterion.PM2,
                fired=True,
                strength=Strength.MODERATE,
                confidence=0.9,
                abstained=False,
                abstention_reason="should not be here",  # not allowed
                evidence=make_empty_bundle(),
                reasoning="...",
            )


# ----------------------- Numeric constraints -----------------------


class TestConfidenceRange:
    @pytest.mark.parametrize("bad_confidence", [-0.01, 1.01, 2.0, -1.0])
    def test_out_of_range_rejected(self, bad_confidence: float) -> None:
        with pytest.raises(ValidationError):
            CriterionOutput(
                criterion=Criterion.PM2,
                fired=True,
                strength=Strength.MODERATE,
                confidence=bad_confidence,
                abstained=False,
                abstention_reason=None,
                evidence=make_empty_bundle(),
                reasoning="...",
            )

    @pytest.mark.parametrize("good_confidence", [0.0, 0.5, 1.0])
    def test_boundary_values_accepted(self, good_confidence: float) -> None:
        out = CriterionOutput(
            criterion=Criterion.PM2,
            fired=True,
            strength=Strength.MODERATE,
            confidence=good_confidence,
            abstained=False,
            abstention_reason=None,
            evidence=make_empty_bundle(),
            reasoning="...",
        )
        assert out.confidence == good_confidence


# ----------------------- CriterionInput -----------------------


class TestCriterionInput:
    def test_input_constructs(self) -> None:
        v = make_variant()
        inp = CriterionInput(
            variant=v,
            gene_context=v.gene,
            evidence_bundle=make_empty_bundle(),
        )
        assert inp.variant.gene.symbol == "BRCA1"

    def test_input_round_trip(self) -> None:
        v = make_variant()
        inp = CriterionInput(
            variant=v,
            gene_context=v.gene,
            evidence_bundle=make_empty_bundle(),
        )
        rebuilt = CriterionInput.model_validate_json(inp.model_dump_json())
        assert rebuilt == inp
