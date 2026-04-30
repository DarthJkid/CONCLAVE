"""Unit tests for CONCLAVE Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from conclave.schemas.audit import AuditTrail, ModelSnapshot
from conclave.schemas.criterion import CriterionOutput, Direction, Strength
from conclave.schemas.evidence import Evidence, EvidenceBundle, EvidenceType, Provenance
from conclave.schemas.variant import GeneContext, HGVS, Variant, Genome


# ── Variant tests ─────────────────────────────────────────────────────────────

class TestVariant:
    def test_basic_construction(self) -> None:
        v = Variant(
            variant_id="13:32339461:A:-",
            chromosome="13",
            position=32339461,
            reference_allele="A",
            alternate_allele="-",
        )
        assert v.chromosome == "13"
        assert v.genome_build == Genome.GRCh38

    def test_chromosome_strips_chr_prefix(self) -> None:
        v = Variant(
            variant_id="chr13:32339461:A:-",
            chromosome="chr13",
            position=32339461,
            reference_allele="A",
            alternate_allele="-",
        )
        assert v.chromosome == "13"

    def test_position_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            Variant(
                variant_id="bad",
                chromosome="1",
                position=0,
                reference_allele="A",
                alternate_allele="T",
            )

    def test_hgvs_whitespace_stripped(self) -> None:
        h = HGVS(cdna="  NM_000059.4:c.5946delT  ")
        assert h.cdna == "NM_000059.4:c.5946delT"


# ── Evidence tests ────────────────────────────────────────────────────────────

class TestEvidenceBundle:
    def _make_provenance(self) -> Provenance:
        return Provenance(source="gnomAD", source_version="4.1")

    def _make_evidence(self, criterion: str = "PM2") -> Evidence:
        return Evidence(
            evidence_id="ev-001",
            evidence_type=EvidenceType.POPULATION,
            criterion=criterion,
            value=0.000001,
            summary="Extremely rare in gnomAD",
            provenance=self._make_provenance(),
        )

    def test_bundle_criterion_mismatch_raises(self) -> None:
        ev = self._make_evidence(criterion="BS1")
        with pytest.raises(ValidationError, match="criterion"):
            EvidenceBundle(variant_id="var-1", criterion="PM2", items=[ev])

    def test_bundle_is_empty(self) -> None:
        bundle = EvidenceBundle(variant_id="var-1", criterion="PM2")
        assert bundle.is_empty

    def test_bundle_add(self) -> None:
        bundle = EvidenceBundle(variant_id="var-1", criterion="PM2")
        ev = self._make_evidence()
        bundle.add(ev)
        assert not bundle.is_empty
        assert len(bundle.items) == 1


# ── CriterionOutput tests ─────────────────────────────────────────────────────

class TestCriterionOutput:
    def test_met_with_strength(self) -> None:
        out = CriterionOutput(
            criterion="PM2",
            met=True,
            strength=Strength.SUPPORTING,
            direction=Direction.PATHOGENIC,
            rationale="Absent from gnomAD",
        )
        assert out.met
        assert out.strength == Strength.SUPPORTING
        assert not out.abstain

    def test_abstention(self) -> None:
        out = CriterionOutput(
            criterion="PM2",
            met=False,
            rationale="Insufficient data",
            abstain=True,
            abstention_reason="gnomAD lookup failed",
        )
        assert out.abstain
        assert out.abstention_reason is not None


# ── AuditTrail tests ──────────────────────────────────────────────────────────

class TestAuditTrail:
    def test_fingerprint_is_deterministic(self) -> None:
        trail = AuditTrail(
            run_id="run-abc",
            variant_id="13:32339461:A:-",
            conclave_version="0.1.0",
        )
        fp1 = trail.compute_fingerprint()
        fp2 = trail.compute_fingerprint()
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex

    def test_finished_before_started_raises(self) -> None:
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError, match="finished_at"):
            AuditTrail(
                run_id="run-xyz",
                variant_id="var-1",
                conclave_version="0.1.0",
                started_at=now,
                finished_at=now - timedelta(seconds=1),
            )
