"""Tests for conclave.schemas.audit.

Coverage:
- Construction via AuditTrail.assemble (the canonical path).
- Frozen-ness, equality, JSON round-trip.
- The hash-integrity validator (the keystone tests of this module).
- Timestamp invariants (order, UTC discipline).
- Criterion-output structural rules (no duplicates, count cap).
- Field-level constraints.
- Determinism: identical inputs produce identical report_ids.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from conclave.schemas.audit import AuditTrail
from conclave.schemas.criterion import (
    Criterion,
    CriterionOutput,
    Strength,
)
from conclave.schemas.evidence import EvidenceBundle
from conclave.schemas.variant import (
    HGVS,
    Chromosome,
    GeneContext,
    GenomicCoordinate,
    Variant,
)
from conclave.schemas.verdict import (
    CalibratedVerdict,
    PathogenicityTier,
    PathogenicityVerdict,
)

# -------------------- Constants --------------------

# Pinned timestamps — never use datetime.now() in tests that compare
# values or hashes. ADR-0004 (determinism contract).
TEST_TIMESTAMP_START = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)
TEST_TIMESTAMP_END = datetime(2026, 5, 9, 12, 30, 0, tzinfo=UTC)


# -------------------- Helpers --------------------


def make_valid_variant() -> Variant:
    """A canonical BRCA1 c.5266dupC variant."""
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


def make_alternate_variant() -> Variant:
    """A different variant, used to prove report_id depends on payload."""
    return Variant(
        hgvs=HGVS(notation="NM_000546.6:c.523C>T"),
        coordinate=GenomicCoordinate(
            chromosome=Chromosome.CHR17,
            position=7_675_088,
            reference="C",
            alternate="T",
        ),
        gene=GeneContext(
            symbol="TP53",
            transcript_id="NM_000546.6",
            is_haploinsufficient=True,
        ),
    )


def make_empty_bundle() -> EvidenceBundle:
    return EvidenceBundle(
        bundle_id="test-bundle",
        items=(),
        assembled_at=TEST_TIMESTAMP_START,
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
        reasoning="Test fixture: criterion fired.",
    )


def make_abstained_output(criterion: Criterion = Criterion.PP1) -> CriterionOutput:
    return CriterionOutput(
        criterion=criterion,
        fired=None,
        strength=None,
        confidence=0.50,
        abstained=True,
        abstention_reason="No evidence available.",
        evidence=make_empty_bundle(),
        reasoning="Test fixture: criterion abstained.",
    )


def make_calibrated_verdict() -> CalibratedVerdict:
    return CalibratedVerdict(
        verdict=PathogenicityVerdict(
            tier=PathogenicityTier.PATHOGENIC,
            tavtigian_score=5.0,
            fired_criteria=(),
            abstained_criteria=(),
            reasoning_summary="Test verdict reasoning.",
        ),
        conformal_alpha=0.10,
        conformal_coverage=0.90,
        calibrator_version="calibrator-v1-test",
        calibrated_at=TEST_TIMESTAMP_START,
    )


def make_valid_audit_trail(
    *,
    variant: Variant | None = None,
    criterion_outputs: tuple[CriterionOutput, ...] | None = None,
    calibrated_verdict: CalibratedVerdict | None = None,
    conclave_version: str = "0.1.0",
    model_identifiers: dict[str, str] | None = None,
    dataset_versions: dict[str, str] | None = None,
    calibrator_version: str = "calibrator-v1-test",
    started_at: datetime = TEST_TIMESTAMP_START,
    completed_at: datetime = TEST_TIMESTAMP_END,
) -> AuditTrail:
    """Construct a valid AuditTrail via assemble().

    Every field is overridable through kwargs (keyword-only). assemble()
    computes the report_id; we never pass one in this helper.
    """
    return AuditTrail.assemble(
        variant=variant if variant is not None else make_valid_variant(),
        criterion_outputs=(
            criterion_outputs
            if criterion_outputs is not None
            else (make_fired_output(), make_abstained_output())
        ),
        calibrated_verdict=(
            calibrated_verdict if calibrated_verdict is not None else make_calibrated_verdict()
        ),
        conclave_version=conclave_version,
        model_identifiers=model_identifiers if model_identifiers is not None else {},
        dataset_versions=dataset_versions if dataset_versions is not None else {},
        calibrator_version=calibrator_version,
        started_at=started_at,
        completed_at=completed_at,
    )


# -------------------- Construction, frozen, round-trip --------------------


class TestAuditTrailConstruction:
    def test_assemble_produces_valid_trail(self) -> None:
        audit = make_valid_audit_trail()
        assert audit.variant.gene.symbol == "BRCA1"
        assert len(audit.criterion_outputs) == 2
        assert audit.criterion_outputs[0].criterion == Criterion.PM2
        assert audit.criterion_outputs[1].abstained is True
        assert len(audit.report_id) == 64
        assert audit.report_id != "0" * 64
        assert audit.started_at == TEST_TIMESTAMP_START
        assert audit.completed_at == TEST_TIMESTAMP_END
        assert audit.completed_at >= audit.started_at

    def test_is_frozen(self) -> None:
        audit = make_valid_audit_trail()
        with pytest.raises(ValidationError):
            audit.conclave_version = "different"

    def test_two_identical_audits_are_equal(self) -> None:
        a = make_valid_audit_trail()
        b = make_valid_audit_trail()
        assert a == b
        # No hash check — AuditTrail contains dict fields (model_identifiers,
        # dataset_versions) which are unhashable. Equality works; hashability
        # would require changing those fields to tuple-of-pairs and is not
        # worth the ergonomic cost. AuditTrails are not put in sets.

    def test_round_trip_through_json(self) -> None:
        original = make_valid_audit_trail()
        rebuilt = AuditTrail.model_validate_json(original.model_dump_json())
        assert rebuilt == original


# -------------------- Hash integrity (the keystone tests) --------------------


class TestReportIdIntegrity:
    """Tests that prove the AuditTrail is self-verifying.

    These are the most important tests in this module. Without these,
    `report_id` is decoration; with them, it is a regulatory-grade
    integrity proof.
    """

    def test_correct_hash_accepted(self) -> None:
        """assemble()'s computed hash satisfies the validator."""
        audit = make_valid_audit_trail()
        # Recompute and verify it matches what assemble produced.
        from conclave.schemas.evidence import sha256_of

        expected = sha256_of(audit._canonical_payload_for_hash())
        assert audit.report_id == expected

    def test_incorrect_hash_rejected(self) -> None:
        """Direct construction with a wrong hash is rejected.

        This is the core integrity proof. Without this test, the
        validator could be silently broken and we would not know.
        """
        with pytest.raises(ValidationError) as exc_info:
            AuditTrail(
                report_id="0" * 64,  # syntactically valid but wrong
                variant=make_valid_variant(),
                calibrated_verdict=make_calibrated_verdict(),
                criterion_outputs=(make_fired_output(), make_abstained_output()),
                conclave_version="0.1.0",
                model_identifiers={},
                dataset_versions={},
                calibrator_version="calibrator-v1-test",
                started_at=TEST_TIMESTAMP_START,
                completed_at=TEST_TIMESTAMP_END,
            )
        assert "integrity" in str(exc_info.value).lower() or "match" in str(exc_info.value).lower()

    @pytest.mark.parametrize(
        ("path", "new_value"),
        [
            (("conclave_version",), "0.2.0-malicious"),
            (("calibrator_version",), "calibrator-v2-evil"),
            (("variant", "gene", "symbol"), "TP53"),
        ],
    )
    def test_tampering_with_payload_invalidates_hash(
        self,
        path: tuple[str, ...],
        new_value: str,
    ) -> None:
        """Tampering with any payload field invalidates the hash.

        This test demonstrates the integrity property end-to-end:
        a 2028 reviewer cannot modify a 2026 report and reconstruct
        a valid AuditTrail from it — the hash will not match.
        """
        audit = make_valid_audit_trail()
        tampered: dict[str, Any] = audit.model_dump(mode="json")

        # Walk the path and mutate the leaf.
        target: Any = tampered
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = new_value

        with pytest.raises(ValidationError):
            AuditTrail.model_validate(tampered)


# -------------------- Timestamp invariants --------------------


class TestTimestamps:
    def test_completed_before_started_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            make_valid_audit_trail(
                started_at=TEST_TIMESTAMP_END,
                completed_at=TEST_TIMESTAMP_START,
            )
        assert "completed_at" in str(exc_info.value) or "started_at" in str(exc_info.value)

    def test_completed_equal_to_started_accepted(self) -> None:
        """Boundary: completed_at == started_at is fine."""
        audit = make_valid_audit_trail(
            started_at=TEST_TIMESTAMP_START,
            completed_at=TEST_TIMESTAMP_START,
        )
        assert audit.started_at == audit.completed_at

    def test_naive_started_at_rejected(self) -> None:
        with pytest.raises((ValidationError, ValueError)) as exc_info:
            make_valid_audit_trail(
                started_at=datetime(2026, 5, 9, 12, 0, 0),  # naive
            )
        assert "timezone" in str(exc_info.value).lower()

    def test_naive_completed_at_rejected(self) -> None:
        with pytest.raises((ValidationError, ValueError)) as exc_info:
            make_valid_audit_trail(
                completed_at=datetime(2026, 5, 9, 12, 30, 0),  # naive
            )
        assert "timezone" in str(exc_info.value).lower()

    def test_non_utc_started_at_coerced_to_utc(self) -> None:
        """A non-UTC tz-aware start time is coerced and validation passes.

        Note the chain: the field validator runs first and coerces;
        then assemble() builds the canonical payload from the
        coerced (UTC) form; the hash matches.
        """
        est = timezone(timedelta(hours=-5))
        # 07:00 EST == 12:00 UTC, matching TEST_TIMESTAMP_START.
        est_start = datetime(2026, 5, 9, 7, 0, 0, tzinfo=est)
        audit = make_valid_audit_trail(started_at=est_start)
        assert audit.started_at.tzinfo == UTC
        assert audit.started_at == TEST_TIMESTAMP_START

    def test_non_utc_completed_at_coerced_to_utc(self) -> None:
        est = timezone(timedelta(hours=-5))
        est_end = datetime(2026, 5, 9, 7, 30, 0, tzinfo=est)
        audit = make_valid_audit_trail(completed_at=est_end)
        assert audit.completed_at.tzinfo == UTC
        assert audit.completed_at == TEST_TIMESTAMP_END


# -------------------- Criterion-output invariants --------------------


class TestCriterionOutputs:
    def test_zero_criteria_accepted(self) -> None:
        """The cap is 'at most 28', not 'exactly 28' — empty is fine."""
        audit = make_valid_audit_trail(criterion_outputs=())
        assert audit.criterion_outputs == ()

    def test_one_criterion_accepted(self) -> None:
        audit = make_valid_audit_trail(
            criterion_outputs=(make_fired_output(),),
        )
        assert len(audit.criterion_outputs) == 1

    def test_duplicate_criterion_rejected(self) -> None:
        """Two CriterionOutputs with the same `criterion` field are rejected.

        We construct two distinct CriterionOutputs both for PM2.
        """
        with pytest.raises(ValidationError) as exc_info:
            make_valid_audit_trail(
                criterion_outputs=(
                    make_fired_output(Criterion.PM2),
                    make_fired_output(Criterion.PM2),
                ),
            )
        assert "duplicate" in str(exc_info.value).lower()

    def test_more_than_28_outputs_rejected(self) -> None:
        """More than 28 outputs is rejected.

        Defence-in-depth note: because Criterion has exactly 28 members,
        constructing 29 outputs requires at least one duplicate. So this
        test trips EITHER the duplicate check OR the count cap. Either
        way, construction fails — the property we care about. We do not
        assert a specific error message.
        """
        all_criteria = list(Criterion)
        outputs = tuple(make_fired_output(c) for c in all_criteria)
        # Add a 29th — necessarily a duplicate of one of the above.
        outputs_with_extra = (*outputs, make_fired_output(Criterion.PM2))
        assert len(outputs_with_extra) == 29
        with pytest.raises(ValidationError):
            make_valid_audit_trail(criterion_outputs=outputs_with_extra)


# -------------------- Field-level constraints --------------------


class TestFieldConstraints:
    @pytest.mark.parametrize(
        "bad_version",
        ["", "has spaces", "has/slashes", 'has"quotes"'],
    )
    def test_invalid_conclave_version_rejected(self, bad_version: str) -> None:
        with pytest.raises(ValidationError):
            make_valid_audit_trail(conclave_version=bad_version)

    def test_invalid_report_id_format_rejected(self) -> None:
        """Constructing AuditTrail directly with a non-hex report_id is rejected.

        This exercises the SHA256Hex pattern constraint (which fires
        BEFORE the integrity validator).
        """
        with pytest.raises(ValidationError):
            AuditTrail(
                report_id="not_a_valid_sha256_hash",
                variant=make_valid_variant(),
                calibrated_verdict=make_calibrated_verdict(),
                criterion_outputs=(make_fired_output(), make_abstained_output()),
                conclave_version="0.1.0",
                model_identifiers={},
                dataset_versions={},
                calibrator_version="calibrator-v1-test",
                started_at=TEST_TIMESTAMP_START,
                completed_at=TEST_TIMESTAMP_END,
            )


# -------------------- Determinism (the regulatory-grade property) --------------------


class TestReportIdDeterminism:
    """If these tests pass, the AuditTrail concept is real.

    The schema-level guarantee: identical inputs → identical report_id.
    The corollary: a 2026 result can be reproduced byte-for-byte in 2028.
    """

    def test_same_inputs_produce_same_report_id(self) -> None:
        a = make_valid_audit_trail()
        b = make_valid_audit_trail()
        assert a.report_id == b.report_id

    def test_different_variants_produce_different_report_ids(self) -> None:
        a = make_valid_audit_trail(variant=make_valid_variant())
        b = make_valid_audit_trail(variant=make_alternate_variant())
        assert a.report_id != b.report_id

    def test_different_timestamps_produce_different_report_ids(self) -> None:
        a = make_valid_audit_trail(
            started_at=TEST_TIMESTAMP_START,
            completed_at=TEST_TIMESTAMP_END,
        )
        b = make_valid_audit_trail(
            started_at=TEST_TIMESTAMP_START,
            completed_at=TEST_TIMESTAMP_END + timedelta(seconds=1),
        )
        assert a.report_id != b.report_id

    def test_different_conclave_version_produces_different_report_ids(self) -> None:
        a = make_valid_audit_trail(conclave_version="0.1.0")
        b = make_valid_audit_trail(conclave_version="0.2.0")
        assert a.report_id != b.report_id
