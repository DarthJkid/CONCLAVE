"""AuditTrail — full reproducibility record for a variant interpretation run."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, model_validator

from conclave.schemas.criterion import CriterionOutput
from conclave.schemas.verdict import CalibratedVerdict, PathogenicityVerdict


class ModelSnapshot(BaseModel):
    """Immutable reference to a specific model version."""

    model_id: str
    provider: str
    snapshot: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class AuditTrail(BaseModel):
    """Complete, reproducible record of a single variant interpretation run."""

    run_id: str = Field(..., description="UUID for this interpretation run")
    variant_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    conclave_version: str = Field(..., description="Version of CONCLAVE used")
    model_snapshots: list[ModelSnapshot] = Field(
        default_factory=list,
        description="All models used in this run, with version pins",
    )
    criterion_outputs: list[CriterionOutput] = Field(default_factory=list)
    verdict: PathogenicityVerdict | None = None
    calibrated_verdict: CalibratedVerdict | None = None
    config_hash: str | None = Field(
        None,
        description="SHA-256 hash of the Hydra config used for this run",
    )
    determinism_seed: int | None = Field(
        None,
        description="Random seed (if any) set for determinism",
    )
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def finished_after_started(self) -> "AuditTrail":
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("finished_at must be after started_at")
        return self

    def compute_fingerprint(self) -> str:
        """Compute a SHA-256 fingerprint of the deterministic fields of this audit trail."""
        payload = {
            "run_id": self.run_id,
            "variant_id": self.variant_id,
            "conclave_version": self.conclave_version,
            "config_hash": self.config_hash,
            "criterion_outputs": [o.model_dump() for o in self.criterion_outputs],
        }
        serialised = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialised.encode()).hexdigest()
