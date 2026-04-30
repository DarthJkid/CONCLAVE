"""Determinism tests: same input → byte-identical output, every time.

These tests catch silent non-determinism — random seeds, dict ordering,
floating-point reordering, model-snapshot drift. They are gates: a
broken determinism test means a result we previously trusted is no
longer reproducible.
"""

from __future__ import annotations

from conclave.schemas.variant import (
    HGVS,
    Chromosome,
    GeneContext,
    GenomicCoordinate,
    Variant,
)


def _canonical_variant() -> Variant:
    """The fixed input. Do not change without an ADR."""
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


# Expected JSON of the canonical variant.
EXPECTED_JSON = (
    '{"hgvs":{"notation":"NM_007294.4:c.5266dupC"},'
    '"coordinate":{"chromosome":"chr17","position":43057062,'
    '"reference":"C","alternate":"CC"},'
    '"gene":{"symbol":"BRCA1","transcript_id":"NM_007294.4",'
    '"is_haploinsufficient":true}}'
)


def test_canonical_variant_serialises_to_known_bytes() -> None:
    """The canonical variant produces the exact expected JSON."""
    variant = _canonical_variant()
    actual = variant.model_dump_json()
    assert actual == EXPECTED_JSON, (
        "Schema serialisation has changed. "
        "If this is intentional: write an ADR, then update EXPECTED_JSON. "
        "If unintentional: a dependency upgrade or schema change has "
        "altered behaviour. Investigate before continuing."
    )


def test_round_trip_is_byte_stable() -> None:
    """Serialise → deserialise → serialise produces identical bytes."""
    original = _canonical_variant()
    once = original.model_dump_json()
    rebuilt = Variant.model_validate_json(once)
    twice = rebuilt.model_dump_json()
    assert once == twice


def test_json_schema_keys_are_stable() -> None:
    """The JSON schema's top-level structure is fixed."""
    schema = Variant.model_json_schema()
    expected_top_level_properties = {"hgvs", "coordinate", "gene"}
    actual = set(schema["properties"].keys())
    assert actual == expected_top_level_properties, (
        f"Variant top-level properties changed: "
        f"added {actual - expected_top_level_properties}, "
        f"removed {expected_top_level_properties - actual}. "
        f"This is a breaking change requiring an ADR."
    )
