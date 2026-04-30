"""Variant schemas: canonical representations of a genetic variant.

A Variant is the input to every criterion agent in CONCLAVE. The contract
defined here is the single source of truth — every other module that touches
a variant imports from this file and never re-defines its shape.

Per ADR-0006, all schemas are Pydantic v2 models with strict validation.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


class Chromosome(StrEnum):
    """The 24 valid human chromosomes plus mitochondrial DNA.

    We use an Enum (rather than a free string) so that an invalid chromosome
    is rejected at construction time.
    """

    CHR1 = "chr1"
    CHR2 = "chr2"
    CHR3 = "chr3"
    CHR4 = "chr4"
    CHR5 = "chr5"
    CHR6 = "chr6"
    CHR7 = "chr7"
    CHR8 = "chr8"
    CHR9 = "chr9"
    CHR10 = "chr10"
    CHR11 = "chr11"
    CHR12 = "chr12"
    CHR13 = "chr13"
    CHR14 = "chr14"
    CHR15 = "chr15"
    CHR16 = "chr16"
    CHR17 = "chr17"
    CHR18 = "chr18"
    CHR19 = "chr19"
    CHR20 = "chr20"
    CHR21 = "chr21"
    CHR22 = "chr22"
    CHRX = "chrX"
    CHRY = "chrY"
    CHRM = "chrM"


# A DNA base must be exactly one of A, C, G, T (we accept lowercase and uppercase).
# We use Annotated + StringConstraints for declarative, schema-visible validation.
DNABase = Annotated[
    str,
    StringConstraints(pattern=r"^[ACGTacgt]+$", min_length=1, max_length=1000),
]


# Gene symbols follow HGNC conventions: uppercase letters, digits, hyphens.
GeneSymbol = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z][A-Z0-9-]{0,15}$", min_length=1, max_length=16),
]


# HGVS notation is the Human Genome Variation Society's standard variant
# nomenclature. Example: "NM_007294.4:c.5266dupC" (BRCA1 transcript,
# coding-sequence position 5266, insertion of C). The full grammar is
# genuinely complex; this regex catches the common cases and we accept
# that exotic forms may need a more sophisticated parser later
# (recorded in calibration_debt.md).
HGVS_PATTERN = re.compile(r"^[A-Z]{1,3}_\d+(\.\d+)?:[cgnmprx]\.[A-Za-z0-9_+\-*>?=()\[\]]+$")


class HGVS(BaseModel):
    """HGVS notation for a variant.

    See https://hgvs-nomenclature.org for the full specification.
    We store the full string and extracted components for downstream use.
    """

    model_config = ConfigDict(
        frozen=True,  # immutable once created
        str_strip_whitespace=True,
        extra="forbid",  # reject unknown fields
    )

    notation: Annotated[
        str,
        StringConstraints(min_length=5, max_length=200),
    ] = Field(
        ...,
        description="The full HGVS string, e.g. 'NM_007294.4:c.5266dupC'.",
    )

    @field_validator("notation")
    @classmethod
    def must_match_hgvs_pattern(cls, value: str) -> str:
        """Reject anything that doesn't look like HGVS notation."""
        if not HGVS_PATTERN.match(value):
            raise ValueError(
                f"'{value}' does not match HGVS notation. "
                f"Expected something like 'NM_007294.4:c.5266dupC'."
            )
        return value


class GenomicCoordinate(BaseModel):
    """A position on the human reference genome (GRCh38/hg38)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chromosome: Chromosome = Field(
        ...,
        description="The chromosome (chr1..chr22, chrX, chrY, chrM).",
    )
    position: Annotated[int, Field(ge=1, le=300_000_000)] = Field(
        ...,
        description="1-based position on the chromosome.",
    )
    reference: DNABase = Field(
        ...,
        description="The reference genome base(s) at this position.",
    )
    alternate: DNABase = Field(
        ...,
        description="The variant base(s) replacing the reference.",
    )

    @field_validator("alternate")
    @classmethod
    def must_differ_from_reference(cls, value: str, info: object) -> str:
        """A variant where ref == alt is not a variant. Reject it."""
        # info.data contains the other already-validated fields
        ref = getattr(info, "data", {}).get("reference")
        if ref is not None and value.upper() == ref.upper():
            raise ValueError(f"alternate ({value}) must differ from reference ({ref}).")
        return value


class GeneContext(BaseModel):
    """Information about the gene a variant lies within.

    This is populated upstream by the variant resolver (VEP wrapper) before
    the criterion agents run. Agents read it as a dependency, never modify it.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: GeneSymbol = Field(..., description="HGNC gene symbol, e.g. 'BRCA1'.")
    transcript_id: Annotated[
        str,
        StringConstraints(pattern=r"^[A-Z]{1,3}_\d+(\.\d+)?$"),
    ] = Field(..., description="MANE-Select transcript, e.g. 'NM_007294.4'.")
    is_haploinsufficient: bool | None = Field(
        None,
        description=(
            "ClinGen-curated haploinsufficiency status. None means unknown / not yet curated."
        ),
    )


class Variant(BaseModel):
    """A canonical variant: HGVS notation + genomic coordinate + gene context.

    This is the unit passed to every criterion agent. Two Variants are equal
    if and only if all their fields are equal — Pydantic gives us this for free
    when frozen=True is set.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    hgvs: HGVS
    coordinate: GenomicCoordinate
    gene: GeneContext
