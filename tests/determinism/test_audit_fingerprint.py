"""Determinism tests — same input must produce byte-for-byte identical output."""

from __future__ import annotations

from conclave.schemas.audit import AuditTrail
from conclave.schemas.criterion import CriterionOutput, Direction, Strength


def _make_trail(criterion_outputs: list[CriterionOutput] | None = None) -> AuditTrail:
    return AuditTrail(
        run_id="determinism-test-run",
        variant_id="13:32339461:A:-",
        conclave_version="0.1.0",
        config_hash="abc123",
        criterion_outputs=criterion_outputs or [],
    )


def test_empty_trail_fingerprint_stable() -> None:
    """The fingerprint of an empty audit trail must be identical across calls."""
    trail = _make_trail()
    fingerprints = [trail.compute_fingerprint() for _ in range(10)]
    assert len(set(fingerprints)) == 1, "Fingerprint is not deterministic"


def test_trail_with_outputs_fingerprint_stable() -> None:
    """Fingerprint must be stable even with criterion outputs."""
    outputs = [
        CriterionOutput(
            criterion="PM2",
            met=True,
            strength=Strength.SUPPORTING,
            direction=Direction.PATHOGENIC,
            rationale="Absent from gnomAD",
        ),
    ]
    trail = _make_trail(criterion_outputs=outputs)
    fp1 = trail.compute_fingerprint()
    fp2 = trail.compute_fingerprint()
    assert fp1 == fp2


def test_different_runs_have_different_fingerprints() -> None:
    """Two audit trails with different run_ids must have different fingerprints."""
    trail_a = AuditTrail(
        run_id="run-a", variant_id="var-1", conclave_version="0.1.0"
    )
    trail_b = AuditTrail(
        run_id="run-b", variant_id="var-1", conclave_version="0.1.0"
    )
    assert trail_a.compute_fingerprint() != trail_b.compute_fingerprint()
