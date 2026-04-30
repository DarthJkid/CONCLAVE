"""Tests for conclave.schemas.variant.

These tests are the executable specification of what a Variant means.
If the schema changes in a way that breaks a test, the change must either
be wrong or be deliberate (and accompanied by an ADR).
"""

from __future__ import annotations

import json

import pytest
from conclave.schemas.variant import (
    HGVS,
    Chromosome,
    GeneContext,
    GenomicCoordinate,
    Variant,
)
from pydantic import ValidationError


# A known-good fixture used across multiple tests.
def make_valid_variant() -> Variant:
    """Construct a canonical, well-formed Variant for BRCA1 c.5266dupC."""
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


class TestVariantConstruction:
    """Positive tests: well-formed inputs produce well-formed Variants."""

    def test_valid_variant_constructs(self) -> None:
        variant = make_valid_variant()
        assert variant.gene.symbol == "BRCA1"
        assert variant.coordinate.chromosome == Chromosome.CHR17
        assert variant.hgvs.notation == "NM_007294.4:c.5266dupC"

    def test_variant_is_frozen(self) -> None:
        """Variants are immutable: assigning to a field raises."""
        variant = make_valid_variant()
        with pytest.raises(ValidationError):
            variant.gene = GeneContext(
                symbol="TP53",
                transcript_id="NM_000546.6",
                is_haploinsufficient=None,
            )

    def test_two_variants_with_same_fields_are_equal(self) -> None:
        """Pydantic gives us value-equality for free when frozen=True."""
        a = make_valid_variant()
        b = make_valid_variant()
        assert a == b
        assert hash(a) == hash(b)


class TestHGVSValidation:
    """Negative tests: malformed HGVS strings are rejected."""

    @pytest.mark.parametrize(
        "bad_notation",
        [
            "this is not HGVS",
            "NM_007294.4",  # missing the :c. part
            "c.5266dupC",  # missing the transcript prefix
            "",
            "NM_007294.4:z.5266dupC",  # 'z' is not a valid HGVS reference type
        ],
    )
    def test_rejects_malformed_notation(self, bad_notation: str) -> None:
        with pytest.raises(ValidationError) as exc_info:
            HGVS(notation=bad_notation)
        # The error message should mention HGVS so a debugger can find it fast.
        assert "HGVS" in str(exc_info.value) or "match" in str(exc_info.value)


class TestGenomicCoordinateValidation:
    """Negative tests on the genomic coordinate."""

    def test_ref_equals_alt_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            GenomicCoordinate(
                chromosome=Chromosome.CHR17,
                position=43_057_062,
                reference="A",
                alternate="A",
            )
        assert "differ" in str(exc_info.value).lower()

    def test_position_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            GenomicCoordinate(
                chromosome=Chromosome.CHR17,
                position=0,
                reference="C",
                alternate="T",
            )

    def test_non_dna_base_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GenomicCoordinate(
                chromosome=Chromosome.CHR17,
                position=43_057_062,
                reference="X",  # X is not a DNA base
                alternate="C",
            )


class TestSerialisation:
    """Round-trip tests: JSON serialisation preserves all information."""

    def test_round_trip_through_json(self) -> None:
        original = make_valid_variant()
        as_json = original.model_dump_json()
        # Sanity: the JSON is parseable.
        parsed = json.loads(as_json)
        assert parsed["gene"]["symbol"] == "BRCA1"
        # Reconstruct and verify equality.
        rebuilt = Variant.model_validate_json(as_json)
        assert rebuilt == original

    def test_json_schema_is_stable(self) -> None:
        """If this test fails, the public schema has changed.

        Schema changes are breaking changes for downstream consumers (the
        FastAPI surface, the LLM structured-output prompts, archived reports).
        Update the snapshot deliberately and write an ADR.
        """
        schema = Variant.model_json_schema()
        # We assert minimum invariants here. Later we'll snapshot the full schema.
        assert "hgvs" in schema["properties"]
        assert "coordinate" in schema["properties"]
        assert "gene" in schema["properties"]
        assert schema["additionalProperties"] is False
