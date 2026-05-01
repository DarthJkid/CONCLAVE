"""Tests for conclave.schemas.verdict.

Coverage: positive construction, frozen-ness, round-trip JSON, malformed
inputs, the cross-field invariants on PathogenicityVerdict, and the
UTC-discipline validator on CalibratedVerdict.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from conclave.schemas.criterion import (
    Criterion,
    CriterionOutput,
    Strength,
)
from conclave.schemas.evidence import EvidenceBundle
from conclave.schemas.verdict import (
    CalibratedVerdict,
    PathogenicityTier,
    PathogenicityVerdict,
)

# -------------------- Constants & helpers --------------------


# A fixed timestamp used everywhere we need a datetime. Never use
# datetime.now() in tests that compare timestamps — two calls produce
# different values. Determinism in tests is the same discipline as
# determinism in production (ADR-0004).
TEST_TIMESTAMP = datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC)


def make_empty_bundle() -> EvidenceBundle:
    """A trivially-empty evidence bundle for tests where we don't care."""
    return EvidenceBundle(
        bundle_id="test-bundle",
        items=(),
        assembled_at=TEST_TIMESTAMP,
    )


def make_fired_output(
    criterion: Criterion = Criterion.PM2,
    strength: Strength = Strength.MODERATE,
) -> CriterionOutput:
    """Build a CriterionOutput in the fired state for use in verdicts."""
    return CriterionOutput(
        criterion=criterion,
        fired=True,
        strength=strength,
        confidence=0.92,
        abstained=False,
        abstention_reason=None,
        evidence=make_empty_bundle(),
        reasoning="Test fixture: criterion fired.",
    )


def make_not_fired_output(
    criterion: Criterion = Criterion.BA1,
) -> CriterionOutput:
    """Build a CriterionOutput in the did-not-fire state."""
    return CriterionOutput(
        criterion=criterion,
        fired=False,
        strength=None,
        confidence=0.95,
        abstained=False,
        abstention_reason=None,
        evidence=make_empty_bundle(),
        reasoning="Test fixture: criterion did not fire.",
    )


def make_abstained_output(
    criterion: Criterion = Criterion.PP1,
) -> CriterionOutput:
    """Build a CriterionOutput in the abstained state."""
    return CriterionOutput(
        criterion=criterion,
        fired=None,
        strength=None,
        confidence=0.50,
        abstained=True,
        abstention_reason="No literature evidence found.",
        evidence=make_empty_bundle(),
        reasoning="Test fixture: criterion abstained.",
    )


def make_valid_verdict(
    *,
    tier: PathogenicityTier = PathogenicityTier.PATHOGENIC,
    tavtigian_score: float = 5.0,
    fired_criteria: tuple[CriterionOutput, ...] = (),
    abstained_criteria: tuple[CriterionOutput, ...] = (),
    reasoning_summary: str = "Test verdict reasoning.",
) -> PathogenicityVerdict:
    """Build a valid PathogenicityVerdict; override any field via kwargs.

    The leading `*` forces all arguments to be keyword-only — there is
    no positional way to call this function. That prevents the bug
    where you swap two arguments by accident and the wrong field is
    set.
    """
    return PathogenicityVerdict(
        tier=tier,
        tavtigian_score=tavtigian_score,
        fired_criteria=fired_criteria,
        abstained_criteria=abstained_criteria,
        reasoning_summary=reasoning_summary,
    )


def make_valid_calibrated_verdict(
    *,
    verdict: PathogenicityVerdict | None = None,
    conformal_alpha: float = 0.10,
    conformal_coverage: float = 0.90,
    calibrator_version: str = "calibrator-v1-test",
    calibrated_at: datetime = TEST_TIMESTAMP,
) -> CalibratedVerdict:
    """Build a valid CalibratedVerdict; override any field via kwargs."""
    return CalibratedVerdict(
        verdict=verdict if verdict is not None else make_valid_verdict(),
        conformal_alpha=conformal_alpha,
        conformal_coverage=conformal_coverage,
        calibrator_version=calibrator_version,
        calibrated_at=calibrated_at,
    )


# -------------------- PathogenicityVerdict — positive paths --------------------


class TestPathogenicityVerdict:
    """Positive construction, frozen, round-trip."""

    def test_constructs_with_no_criteria(self) -> None:
        verdict = make_valid_verdict()
        assert verdict.tier == PathogenicityTier.PATHOGENIC
        assert verdict.tavtigian_score == 5.0
        assert verdict.fired_criteria == ()
        assert verdict.abstained_criteria == ()

    def test_constructs_with_fired_and_abstained(self) -> None:
        verdict = make_valid_verdict(
            fired_criteria=(make_fired_output(Criterion.PM2),),
            abstained_criteria=(make_abstained_output(Criterion.PP1),),
        )
        assert len(verdict.fired_criteria) == 1
        assert len(verdict.abstained_criteria) == 1
        assert verdict.fired_criteria[0].criterion == Criterion.PM2
        assert verdict.abstained_criteria[0].criterion == Criterion.PP1

    def test_is_frozen(self) -> None:
        verdict = make_valid_verdict()
        with pytest.raises(ValidationError):
            verdict.tavtigian_score = 3.0

    def test_two_identical_verdicts_are_equal(self) -> None:
        a = make_valid_verdict()
        b = make_valid_verdict()
        assert a == b
        assert hash(a) == hash(b)

    def test_round_trip_through_json(self) -> None:
        original = make_valid_verdict(
            fired_criteria=(make_fired_output(),),
            abstained_criteria=(make_abstained_output(),),
        )
        rebuilt = PathogenicityVerdict.model_validate_json(original.model_dump_json())
        assert rebuilt == original


# -------------------- PathogenicityVerdict — score boundary --------------------


class TestTavtigianScoreBoundary:
    """Boundary tests on the tavtigian_score field.

    Boundary tests verify that the schema accepts values *at* the limit
    and rejects values *just past* the limit. They catch off-by-one bugs
    that 'way out of range' tests miss.
    """

    @pytest.mark.parametrize("good_score", [-50.0, -10.5, 0.0, 25.0, 50.0])
    def test_in_range_accepted(self, good_score: float) -> None:
        verdict = make_valid_verdict(tavtigian_score=good_score)
        assert verdict.tavtigian_score == good_score

    @pytest.mark.parametrize("bad_score", [-50.01, -100.0, 50.01, 1500.0])
    def test_out_of_range_rejected(self, bad_score: float) -> None:
        with pytest.raises(ValidationError):
            make_valid_verdict(tavtigian_score=bad_score)


# -------------------- PathogenicityVerdict — invalid tier --------------------


class TestTierValidation:
    def test_invalid_tier_string_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PathogenicityVerdict(
                tier="not_a_valid_tier",  # type: ignore[arg-type]
                tavtigian_score=0.0,
                fired_criteria=(),
                abstained_criteria=(),
                reasoning_summary="...",
            )


# -------------------- PathogenicityVerdict — cross-field invariants --------------------


class TestPathogenicityVerdictInvariants:
    """The @model_validator on PathogenicityVerdict enforces three rules:

    1. Every entry in fired_criteria has fired=True.
    2. Every entry in abstained_criteria has abstained=True (fired is None).
    3. The criteria sets are disjoint.

    Each rule has its own test.
    """

    def test_fired_list_with_non_fired_entry_rejected(self) -> None:
        """Rule 1: fired_criteria cannot contain a fired=False output."""
        with pytest.raises(ValidationError) as exc_info:
            make_valid_verdict(
                fired_criteria=(make_not_fired_output(Criterion.BA1),),
            )
        assert "fired" in str(exc_info.value).lower()

    def test_fired_list_with_abstained_entry_rejected(self) -> None:
        """Rule 1, second variant: an abstained output is also not 'fired'."""
        with pytest.raises(ValidationError):
            make_valid_verdict(
                fired_criteria=(make_abstained_output(Criterion.PP1),),
            )

    def test_abstained_list_with_non_abstained_entry_rejected(self) -> None:
        """Rule 2: abstained_criteria cannot contain a fired=True output."""
        with pytest.raises(ValidationError) as exc_info:
            make_valid_verdict(
                abstained_criteria=(make_fired_output(Criterion.PM2),),
            )
        assert "abstain" in str(exc_info.value).lower()

    def test_overlap_between_fired_and_abstained_rejected(self) -> None:
        """Rule 3: a criterion cannot appear in both lists.

        We construct each criterion in the appropriate state — PM2 fires
        in fired_criteria, PM2 abstains in abstained_criteria — so
        rules 1 and 2 are satisfied individually, and only the disjoint
        rule should reject.
        """
        with pytest.raises(ValidationError) as exc_info:
            make_valid_verdict(
                fired_criteria=(make_fired_output(Criterion.PM2),),
                abstained_criteria=(make_abstained_output(Criterion.PM2),),
            )
        assert "both" in str(exc_info.value).lower() or "overlap" in str(exc_info.value).lower()


# -------------------- CalibratedVerdict — positive paths --------------------


class TestCalibratedVerdict:
    def test_constructs(self) -> None:
        cv = make_valid_calibrated_verdict()
        assert cv.verdict.tier == PathogenicityTier.PATHOGENIC
        assert cv.conformal_alpha == 0.10
        assert cv.conformal_coverage == 0.90
        assert cv.calibrator_version == "calibrator-v1-test"
        assert cv.calibrated_at == TEST_TIMESTAMP

    def test_is_frozen(self) -> None:
        cv = make_valid_calibrated_verdict()
        with pytest.raises(ValidationError):
            cv.conformal_alpha = 0.05

    def test_round_trip_through_json(self) -> None:
        original = make_valid_calibrated_verdict(
            verdict=make_valid_verdict(
                fired_criteria=(make_fired_output(),),
            ),
        )
        rebuilt = CalibratedVerdict.model_validate_json(original.model_dump_json())
        assert rebuilt == original


# -------------------- CalibratedVerdict — alpha and coverage ranges --------------------


class TestConformalAlphaRange:
    """conformal_alpha is constrained to (0.0, 1.0) — both bounds STRICT."""

    @pytest.mark.parametrize("good_alpha", [0.001, 0.05, 0.10, 0.50, 0.99])
    def test_in_range_accepted(self, good_alpha: float) -> None:
        cv = make_valid_calibrated_verdict(
            conformal_alpha=good_alpha,
            conformal_coverage=1.0 - good_alpha,
        )
        assert cv.conformal_alpha == good_alpha

    @pytest.mark.parametrize("bad_alpha", [-0.1, 0.0, 1.0, 1.5])
    def test_out_of_range_rejected(self, bad_alpha: float) -> None:
        with pytest.raises(ValidationError):
            make_valid_calibrated_verdict(conformal_alpha=bad_alpha)


class TestConformalCoverageRange:
    """conformal_coverage is constrained to [0.0, 1.0] — both bounds INCLUSIVE."""

    @pytest.mark.parametrize("good_coverage", [0.0, 0.5, 0.90, 1.0])
    def test_in_range_accepted(self, good_coverage: float) -> None:
        cv = make_valid_calibrated_verdict(conformal_coverage=good_coverage)
        assert cv.conformal_coverage == good_coverage

    @pytest.mark.parametrize("bad_coverage", [-0.001, 1.001, 16.0])
    def test_out_of_range_rejected(self, bad_coverage: float) -> None:
        with pytest.raises(ValidationError):
            make_valid_calibrated_verdict(conformal_coverage=bad_coverage)


# -------------------- CalibratedVerdict — UTC discipline --------------------


class TestCalibratedAtUTCDiscipline:
    def test_naive_datetime_rejected(self) -> None:
        naive = datetime(2026, 4, 30, 12, 0, 0)  # no tzinfo
        with pytest.raises(ValidationError) as exc_info:
            make_valid_calibrated_verdict(calibrated_at=naive)
        assert "timezone" in str(exc_info.value).lower()

    def test_non_utc_timezone_is_coerced_to_utc(self) -> None:
        from datetime import timedelta, timezone

        est = timezone(timedelta(hours=-5))
        est_timestamp = datetime(2026, 4, 30, 7, 0, 0, tzinfo=est)
        cv = make_valid_calibrated_verdict(calibrated_at=est_timestamp)
        assert cv.calibrated_at.tzinfo == UTC


# -------------------- CalibratedVerdict — calibrator_version pattern --------------------


class TestCalibratorVersion:
    @pytest.mark.parametrize(
        "good_version",
        [
            "v1",
            "calibrator-v2-stratified-2026-04",
            "0.1.0",
            "test_run.42",
        ],
    )
    def test_valid_versions_accepted(self, good_version: str) -> None:
        cv = make_valid_calibrated_verdict(calibrator_version=good_version)
        assert cv.calibrator_version == good_version

    @pytest.mark.parametrize(
        "bad_version",
        [
            "",  # empty
            "has spaces",
            "has/slashes",
            'has"quotes"',
        ],
    )
    def test_invalid_versions_rejected(self, bad_version: str) -> None:
        with pytest.raises(ValidationError):
            make_valid_calibrated_verdict(calibrator_version=bad_version)
