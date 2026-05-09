"""Audit Trail:
The AuditTrail is the full reproducibility record of a single CONCLAVE interpretation.
It binds together:

- The variant that was interpreted.
- The calibrated verdict.
- All criterion outputs (the 28 of them, including abstentions).
- The set of model identifiers used (LLM, embedding, NLI).
- The set of dataset versions referenced.
- A high-resolution timestamp.
- A report_id that is the SHA-256 of a canonical serialisation of all the above
(so the report is its own integrity proof).


"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from conclave.schemas.criterion import Criterion, CriterionOutput
from conclave.schemas.evidence import ModelIdentifier, SHA256Hex, sha256_of
from conclave.schemas.variant import Variant
from conclave.schemas.verdict import CalibratedVerdict


class AuditTrail(BaseModel):
    """The full reproducible record of agentic decisions"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    report_id: SHA256Hex = Field(
        ...,
        description=(
            "SHA-256 hex digest of the canonical serialisation of every other "
            "field. This is the audit trail's integrity proof — recompute it "
            "to verify the report has not been tampered with."
        ),
    )

    variant: Variant

    calibrated_verdict: CalibratedVerdict

    criterion_outputs: tuple[CriterionOutput, ...]

    # Versioning
    conclave_version: Annotated[
        str, StringConstraints(pattern=r"^[A-Za-z0-9._-]+$", min_length=1, max_length=50)
    ] = Field(
        ...,
        description="Version tag of the conclave system",
    )

    model_identifiers: dict[str, ModelIdentifier]

    dataset_versions: dict[str, str]

    calibrator_version: str

    # Timing
    started_at: datetime = Field(..., description="The datetime at which the agent task began.")

    completed_at: datetime = Field(..., description="The datetime the agent task completed/ended.")

    @field_validator("started_at", "completed_at")
    @classmethod
    def must_be_utc(cls, value: datetime) -> datetime:
        """Naive datetimes are rejected; non-UTC tz-aware values are coerced to UTC."""
        if value.tzinfo is None:
            raise ValueError("Audit timestamps must be timezone-aware (UTC).")
        if value.tzinfo != UTC:
            return value.astimezone(UTC)
        return value

        # invariants:

    # - completed_at >= started_at
    # - len(criterion_outputs) <= 28 (could be less in tests; production validates ==28)
    # - criterion_outputs has at most one entry per criterion (no duplicates)
    # - report_id == sha256_of(canonical_serialisation_of_other_fields)
    @model_validator(mode="after")
    def check_invariants(self) -> AuditTrail:
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must be >= started_at.")

        if len(self.criterion_outputs) > 28:
            raise ValueError(
                f"criterion_outputs has {len(self.criterion_outputs)} entries; expected at most 28."
            )

        seen: set[Criterion] = set()
        for output in self.criterion_outputs:
            if output.criterion in seen:
                raise ValueError(f"Duplicate criterion output for {output.criterion}.")
            seen.add(output.criterion)

        expected_hash = sha256_of(self._canonical_payload_for_hash())
        if self.report_id != expected_hash:
            print("=" * 60)
            print("CANONICAL FROM VALIDATOR:")
            print(self._canonical_payload_for_hash())
            print("=" * 60)
            raise ValueError(
                f"report_id ({self.report_id[:16]}...) does not match the SHA-256 "
                f"of the canonical payload ({expected_hash[:16]}...). "
                f"Audit trail integrity violated."
            )
        return self

    def _canonical_payload_for_hash(self) -> str:
        """Return a canonical JSON serialisation of all fields except report_id."""
        payload = self.model_dump(mode="json", exclude={"report_id"})
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @classmethod
    def assemble(
        cls,
        *,
        variant: Variant,
        calibrated_verdict: CalibratedVerdict,
        criterion_outputs: tuple[CriterionOutput, ...],
        conclave_version: str,
        model_identifiers: dict[str, str],
        dataset_versions: dict[str, str],
        calibrator_version: str,
        started_at: datetime,
        completed_at: datetime,
    ) -> AuditTrail:
        """Compute report_id and construct the AuditTrail in one step.

        Uses model_construct to build a temporary instance that bypasses
        validation, which lets us call _canonical_payload_for_hash on the
        same serialisation path the integrity validator uses. That makes
        both canonical strings byte-identical and the hashes match.
        """
        # Coerce timestamps to UTC up front (matches the field validator).
        if started_at.tzinfo is None:
            raise ValueError("started_at must be timezone-aware (UTC).")
        if completed_at.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware (UTC).")
        started_at_utc = started_at.astimezone(UTC)
        completed_at_utc = completed_at.astimezone(UTC)

        # Build a temp instance bypassing validation — model_construct skips
        # ALL validators, including the integrity check. We only need this
        # instance to compute the canonical payload via the same code path
        # the validator will use.
        placeholder = "0" * 64
        temp = cls.model_construct(
            report_id=placeholder,
            variant=variant,
            calibrated_verdict=calibrated_verdict,
            criterion_outputs=criterion_outputs,
            conclave_version=conclave_version,
            model_identifiers=model_identifiers,
            dataset_versions=dataset_versions,
            calibrator_version=calibrator_version,
            started_at=started_at_utc,
            completed_at=completed_at_utc,
        )
        real_hash = sha256_of(temp._canonical_payload_for_hash())

        # Construct properly — validation runs, hash matches, instance returned.
        return cls(
            report_id=real_hash,
            variant=variant,
            calibrated_verdict=calibrated_verdict,
            criterion_outputs=criterion_outputs,
            conclave_version=conclave_version,
            model_identifiers=model_identifiers,
            dataset_versions=dataset_versions,
            calibrator_version=calibrator_version,
            started_at=started_at_utc,
            completed_at=completed_at_utc,
        )
