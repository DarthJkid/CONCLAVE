"""Evidence, Provenance, and EvidenceBundle Pydantic models."""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class EvidenceType(StrEnum):
    POPULATION = "population"
    COMPUTATIONAL = "computational"
    FUNCTIONAL = "functional"
    SEGREGATION = "segregation"
    ALLELIC = "allelic"
    DE_NOVO = "de_novo"
    LITERATURE = "literature"
    CLINICAL = "clinical"


class Provenance(BaseModel):
    """Tracks where a piece of evidence came from."""

    source: str = Field(..., description="Data source name, e.g. 'gnomAD', 'ClinVar', 'PubMed'")
    source_version: str | None = Field(None, description="Version or release of the data source")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    url: str | None = None
    query: str | None = Field(None, description="The query or API call used to retrieve this evidence")
    raw_response_hash: str | None = Field(
        None,
        description="SHA-256 hex digest of the raw API response for auditability",
    )

    @classmethod
    def from_raw(cls, source: str, raw: str, **kwargs: Any) -> "Provenance":
        """Create a Provenance record with a hash of the raw response."""
        digest = hashlib.sha256(raw.encode()).hexdigest()
        return cls(source=source, raw_response_hash=digest, **kwargs)


class Evidence(BaseModel):
    """A single piece of evidence relevant to a criterion evaluation."""

    evidence_id: str = Field(..., description="Unique identifier for this evidence item")
    evidence_type: EvidenceType
    criterion: str = Field(..., description="ACMG/AMP criterion this evidence pertains to, e.g. PM2")
    value: Any = Field(..., description="The actual evidence value (allele frequency, score, etc.)")
    summary: str = Field(..., description="Human-readable summary of the evidence")
    provenance: Provenance
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the accuracy of this evidence item",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    """All evidence collected for evaluating a single criterion on a single variant."""

    variant_id: str
    criterion: str
    items: list[Evidence] = Field(default_factory=list)
    assembled_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def check_consistent_criterion(self) -> "EvidenceBundle":
        for item in self.items:
            if item.criterion != self.criterion:
                raise ValueError(
                    f"Evidence item {item.evidence_id} has criterion {item.criterion!r} "
                    f"but bundle criterion is {self.criterion!r}"
                )
        return self

    def add(self, item: Evidence) -> None:
        """Append an evidence item to the bundle."""
        self.items.append(item)

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0
