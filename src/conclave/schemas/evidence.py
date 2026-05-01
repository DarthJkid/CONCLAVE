"""Evidence schemas: canonical representations of a genetic variant.

The structure that holds every claim made by every agent, with its source URI, retrieval timestamp

Per ADR-0006, all schemas are Pydantic v2 models with strict validation.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


class SourceKind(StrEnum):
    """The closed set of evidence source types that CONCLAVE recognizes."""

    PUBMED = "pubmed"
    CLINVAR = "clinvar"
    GNOMAD = "gnomad"
    CLINGEN = "clingen"
    UNIPROT = "uniprot"
    DBNSFP = "dbnsfp"
    ALPHAMISSENSE = "alphamissense"
    SPLICEAI = "spliceai"
    MANUAL = "manual"

    # We use an Enum (rather than a free string) so that an invalid source kind
    # is REJECTED at construction time.


# A SHA-256 hex digest is exactly 64 characters long and consists of hexadecimals
SHA256Hex = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9a-f]{64}$", min_length=64, max_length=64),
]

# A "model identifier" is a name plus a SHA-256 of the weights or a
# released-snapshot identifier. Format: "name@sha256:hex" or "name@version-tag".
ModelIdentifier = Annotated[
    str,
    StringConstraints(
        pattern=r"^[A-Za-z0-9._/-]+@(?:sha256:[0-9a-f]{64}|[A-Za-z0-9._-]+)$",
        min_length=10,
        max_length=200,
    ),
]


def sha256_of(text: str) -> str:
    """Compute the SHA-256 hex digest of the given UTF-8 text.
    Used by test and by Provenance.from_snippet() to produce stable hashes
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Provenance(BaseModel):
    """A piece of evidence for a claim, with its source and retrieval timestamp.
    Two Provenance objects are equal if and only if all their fields are
    equal — frozen=True gives us this automatically.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        frozen=True,
    )

    source_uri: AnyUrl = Field(
        ...,
        description="The URI from which this evidence was retrieved (e.g. a PubMed abstract URL).",
    )

    source_kind: SourceKind = Field(
        ...,
        description="The kind of source from which this evidence was retrieved.",
    )

    retrieval_timestamp: datetime = Field(
        ...,
        description="The UTC timestamp when this evidence was retrieved.",
    )

    snippet: Annotated[str, StringConstraints(min_length=1, max_length=10_000)] = Field(
        ...,
        description="The text snippet from the source that supports the claim.",
    )

    snippet_hash: SHA256Hex = Field(
        ...,
        description="The SHA-256 hex digest of the snippet, for integrity verification.",
    )

    retriever_version: Annotated[
        str,
        StringConstraints(pattern=r"^[A-Za-z0-9._-]+$", min_length=1, max_length=50),
    ] = Field(
        ...,
        description="Version tag of the retrieval index tool/index used (e.g. pubmed-2026-04).",
    )

    embedding_model: ModelIdentifier | None = Field(
        None,
        description=(
            "Embedding model identifier when the claim was found via RAG. "
            "None when retrieval is direct (e.g. ClinVar lookup by accession, "
            "or PubMed search by PMID)."
        ),
    )

    nli_model: ModelIdentifier | None = Field(
        None,
        description=(
            "NLI model identifier when the claim has been verified by the "
            "citation verifier. None when verification has not (yet) occurred."
        ),
    )

    @field_validator("retrieval_timestamp")
    @classmethod
    def must_be_timezone_aware_utc(cls, value: datetime) -> datetime:
        """Reject naive datetimes or those with non-UTC timezones."""
        if value.tzinfo is None:
            raise ValueError(
                "retrieval_timestamp must be timezone-aware (UTC). "
                "Naive datetimes are not accepted."
            )
        if value.tzinfo != UTC:
            # Coerce: a non-UTC timezone is not rejected outright, but converted to UTC.
            return value.astimezone(UTC)
        return value

    @model_validator(mode="after")
    def hash_must_match_snippet(self) -> Provenance:
        """Cross-field validation to ensure that snippet_has equals the SHA-256 hash of snippet."""
        expected = sha256_of(self.snippet)
        if self.snippet_hash != expected:
            raise ValueError(
                f"snippet_hash ({self.snippet_hash[:16]}...) does not match "
                f"SHA-256 hash of snippet ({expected[:16]}...). "
                f"Please ensure the integrity of the snippet and its hash."
            )
        return self

    @classmethod
    def from_snippet(
        cls,
        *,
        source_uri: str,
        source_kind: SourceKind,
        snippet: str,
        retriever_version: str,
        retrieval_timestamp: datetime | None = None,
        embedding_model: str | None = None,
        nli_model: str | None = None,
    ) -> Provenance:
        """Convenience constructor that computes the snippet_has automatically from the snippet."""
        ts = retrieval_timestamp if retrieval_timestamp is not None else datetime.now(UTC)
        return cls(
            source_uri=AnyUrl(source_uri),
            source_kind=source_kind,
            retrieval_timestamp=ts,
            snippet=snippet,
            snippet_hash=sha256_of(snippet),
            retriever_version=retriever_version,
            embedding_model=embedding_model,
            nli_model=nli_model,
        )


class Evidence(BaseModel):
    """A claim with its provenance capsule and any structured data extracted."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    claim: Annotated[str, StringConstraints(min_length=1, max_length=2000)] = Field(
        ...,
        description="A short structured statement of what was found.",
    )

    provenance: Provenance = Field(
        ...,
        description=(
            "Where the claim from, when, and a hash of the source snippet that supports it."
        ),
    )

    extracted_data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Free-form structured data extracted from the snippet. "
            "Examples: {'allele_frequency': 0.001}, {'family_count': 3}. "
            "Type is intentionally open for agents to serialise their own structures."
        ),
    )


class EvidenceBundle(BaseModel):
    """A collection of evidence items, typically associated with one criterion run."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    bundle_id: Annotated[
        str,
        StringConstraints(pattern=r"^[A-Za-z0-9._-]+$", min_length=1, max_length=100),
    ] = Field(
        ...,
        description="Stable identifier for this bundle (e.g. 'PM2-BRCA1-c5266dupC-001').",
    )
    items: tuple[Evidence, ...] = Field(
        default_factory=tuple,
        description=(
            "Evidence items in this bundle. We use tuple (not list) so the "
            "bundle is hashable and immutable."
        ),
    )
    assembled_at: datetime = Field(
        ...,
        description="UTC timestamp when this bundle was assembled.",
    )

    @field_validator("assembled_at")
    @classmethod
    def must_be_timezone_aware_utc(cls, value: datetime) -> datetime:
        """Reject naive datetimes or those with non-UTC timezones."""
        if value.tzinfo is None:
            raise ValueError("assembled_at must be timezone-aware (UTC).")
        if value.tzinfo != UTC:
            # Coerce: a non-UTC timezone is not rejected outright, but converted to UTC.
            return value.astimezone(UTC)
        return value

    @property
    def empty(self) -> bool:
        """True if this bundle contains no evidence items."""
        return len(self.items) == 0
