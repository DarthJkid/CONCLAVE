"""Tests for conclave.schemas.evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timezone

import pytest
from pydantic import ValidationError

from conclave.schemas.evidence import (
    Evidence,
    EvidenceBundle,
    Provenance,
    SourceKind,
    sha256_of,
)

# ----------------------- Fixtures -----------------------


def make_provenance(
    snippet: str = "Allele frequency in gnomAD v4 is 0.00001.",
) -> Provenance:
    """A canonical Provenance for tests; mutate via from_snippet kwargs as needed."""
    return Provenance.from_snippet(
        source_uri="https://gnomad.broadinstitute.org/variant/17-43057062-C-CC",
        source_kind=SourceKind.GNOMAD,
        snippet=snippet,
        retriever_version="gnomad-v4-2026-04",
        retrieval_timestamp=datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC),
    )


def make_evidence() -> Evidence:
    return Evidence(
        claim="Allele frequency 0.00001 in gnomAD v4.",
        provenance=make_provenance(),
        extracted_data={"allele_frequency": 0.00001, "allele_count": 2},
    )


# ----------------------- Provenance -----------------------


class TestProvenanceConstruction:
    def test_from_snippet_computes_hash(self) -> None:
        prov = make_provenance()
        assert prov.snippet_hash == sha256_of(prov.snippet)
        assert len(prov.snippet_hash) == 64

    def test_provenance_is_frozen(self) -> None:
        prov = make_provenance()
        with pytest.raises(ValidationError):
            prov.snippet = "tampered"

    def test_two_identical_provenances_are_equal(self) -> None:
        a = make_provenance()
        b = make_provenance()
        assert a == b
        assert hash(a) == hash(b)


class TestProvenanceValidation:
    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Provenance.from_snippet(
                source_uri="https://example.com/x",
                source_kind=SourceKind.MANUAL,
                snippet="x",
                retriever_version="v1",
                retrieval_timestamp=datetime(2026, 4, 30, 12, 0, 0),  # naive
            )
        assert "timezone-aware" in str(exc_info.value)

    def test_non_utc_timezone_is_coerced(self) -> None:
        """A timestamp in a non-UTC timezone is coerced to UTC."""
        from datetime import timedelta

        est = timezone(timedelta(hours=-5))
        prov = Provenance.from_snippet(
            source_uri="https://example.com/x",
            source_kind=SourceKind.MANUAL,
            snippet="x",
            retriever_version="v1",
            retrieval_timestamp=datetime(2026, 4, 30, 7, 0, 0, tzinfo=est),
        )
        assert prov.retrieval_timestamp.tzinfo == UTC

    def test_hash_mismatch_rejected(self) -> None:
        """Constructing Provenance directly with a wrong hash must fail."""
        from pydantic import AnyUrl

        with pytest.raises(ValidationError) as exc_info:
            Provenance(
                source_uri=AnyUrl("https://example.com/x"),
                source_kind=SourceKind.MANUAL,
                retrieval_timestamp=datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC),
                snippet="hello world",
                snippet_hash="0" * 64,  # wrong — should be SHA-256 of "hello world"
                retriever_version="v1",
                embedding_model=None,
                nli_model=None,
            )
        assert "integrity" in str(exc_info.value).lower() or "match" in str(exc_info.value).lower()

    @pytest.mark.parametrize(
        "bad_uri",
        ["not a url", "ftp://", "://missing-scheme", ""],
    )
    def test_malformed_uri_rejected(self, bad_uri: str) -> None:
        with pytest.raises(ValidationError):
            Provenance.from_snippet(
                source_uri=bad_uri,
                source_kind=SourceKind.MANUAL,
                snippet="x",
                retriever_version="v1",
            )

    def test_invalid_model_identifier_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Provenance.from_snippet(
                source_uri="https://example.com/x",
                source_kind=SourceKind.MANUAL,
                snippet="x",
                retriever_version="v1",
                embedding_model="just-a-name-no-version",  # missing @...
            )


class TestProvenanceSerialisation:
    def test_round_trip_through_json(self) -> None:
        original = make_provenance()
        rebuilt = Provenance.model_validate_json(original.model_dump_json())
        assert rebuilt == original


# ----------------------- Evidence -----------------------


class TestEvidence:
    def test_evidence_constructs(self) -> None:
        ev = make_evidence()
        assert ev.claim.startswith("Allele frequency")
        assert ev.extracted_data["allele_frequency"] == 0.00001

    def test_evidence_is_frozen(self) -> None:
        ev = make_evidence()
        with pytest.raises(ValidationError):
            ev.claim = "different claim"

    def test_extracted_data_defaults_to_empty(self) -> None:
        ev = Evidence(claim="trivial", provenance=make_provenance())
        assert ev.extracted_data == {}

    def test_round_trip_through_json(self) -> None:
        ev = make_evidence()
        rebuilt = Evidence.model_validate_json(ev.model_dump_json())
        assert rebuilt == ev


# ----------------------- EvidenceBundle -----------------------


class TestEvidenceBundle:
    def test_empty_bundle(self) -> None:
        bundle = EvidenceBundle(
            bundle_id="test-001",
            items=(),
            assembled_at=datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC),
        )
        assert bundle.empty is True
        assert len(bundle.items) == 0

    def test_non_empty_bundle(self) -> None:
        bundle = EvidenceBundle(
            bundle_id="test-002",
            items=(make_evidence(), make_evidence()),
            assembled_at=datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC),
        )
        assert bundle.empty is False
        assert len(bundle.items) == 2

    def test_naive_assembled_at_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EvidenceBundle(
                bundle_id="test-003",
                items=(),
                assembled_at=datetime(2026, 4, 30, 12, 0, 0),  # naive
            )

    @pytest.mark.parametrize(
        "bad_id",
        ["", "has spaces", "has/slashes", 'has"quotes"'],
    )
    def test_bundle_id_validation(self, bad_id: str) -> None:
        with pytest.raises(ValidationError):
            EvidenceBundle(
                bundle_id=bad_id,
                items=(),
                assembled_at=datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC),
            )

    def test_bundle_round_trip(self) -> None:
        bundle = EvidenceBundle(
            bundle_id="test-004",
            items=(make_evidence(),),
            assembled_at=datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC),
        )
        rebuilt = EvidenceBundle.model_validate_json(bundle.model_dump_json())
        assert rebuilt == bundle


# ----------------------- Helper function tests -----------------------


class TestSha256Helper:
    def test_known_hash(self) -> None:
        # SHA-256 of "hello world" is a well-known value.
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert sha256_of("hello world") == expected

    def test_empty_string(self) -> None:
        # SHA-256 of empty string is also a well-known value.
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert sha256_of("") == expected
