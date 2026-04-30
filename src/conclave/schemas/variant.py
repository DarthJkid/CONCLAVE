"""Variant, GeneContext, and HGVS Pydantic models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Genome(StrEnum):
    GRCh37 = "GRCh37"
    GRCh38 = "GRCh38"


class HGVS(BaseModel):
    """Human Genome Variation Society nomenclature for a sequence variant."""

    cdna: str | None = Field(None, description="cDNA-level notation, e.g. NM_000059.4:c.5946delT")
    protein: str | None = Field(None, description="Protein-level notation, e.g. NP_000050.3:p.Ser1982fs")
    genomic: str | None = Field(None, description="gDNA-level notation, e.g. NC_000013.11:g.32339461delA")

    @field_validator("cdna", "protein", "genomic", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) else v


class GeneContext(BaseModel):
    """Gene-level context relevant to variant interpretation."""

    gene_symbol: str = Field(..., description="HGNC-approved gene symbol, e.g. BRCA2")
    hgnc_id: str | None = Field(None, description="HGNC numeric identifier, e.g. HGNC:1101")
    omim_ids: list[str] = Field(default_factory=list, description="Associated OMIM MIM numbers")
    inheritance_modes: list[str] = Field(
        default_factory=list,
        description="Inheritance modes, e.g. ['autosomal_dominant', 'autosomal_recessive']",
    )
    moi_confident: bool = Field(
        False,
        description="True when the mode of inheritance for this disease context is well-established",
    )


class Variant(BaseModel):
    """Canonical representation of a genomic variant under evaluation."""

    variant_id: str = Field(
        ...,
        description="Internal identifier, e.g. chr13:32339461:A:- (genome-build-agnostic key)",
    )
    chromosome: str = Field(..., description="Chromosome, e.g. '13' or 'chrX'")
    position: int = Field(..., ge=1, description="1-based genomic position")
    reference_allele: str = Field(..., min_length=1)
    alternate_allele: str = Field(..., min_length=1)
    genome_build: Genome = Field(Genome.GRCh38)
    hgvs: HGVS = Field(default_factory=HGVS)
    gene_context: GeneContext | None = None
    rsid: str | None = Field(None, description="dbSNP rsID if available")

    @field_validator("chromosome", mode="before")
    @classmethod
    def normalise_chromosome(cls, v: str) -> str:
        """Strip leading 'chr' prefix for uniformity."""
        return v.removeprefix("chr")
