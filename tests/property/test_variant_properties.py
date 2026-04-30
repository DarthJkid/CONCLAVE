"""Hypothesis-based property tests for Variant and HGVS schemas."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from conclave.schemas.variant import HGVS, Variant, Genome


@given(
    chrom=st.sampled_from(["1", "2", "chr1", "chrX", "Y", "chrMT"]),
    pos=st.integers(min_value=1, max_value=250_000_000),
    ref=st.text(alphabet="ACGT", min_size=1, max_size=10),
    alt=st.text(alphabet="ACGT-", min_size=1, max_size=10),
)
@settings(max_examples=200)
def test_variant_always_strips_chr_prefix(chrom: str, pos: int, ref: str, alt: str) -> None:
    v = Variant(
        variant_id=f"{chrom}:{pos}:{ref}:{alt}",
        chromosome=chrom,
        position=pos,
        reference_allele=ref,
        alternate_allele=alt,
    )
    assert not v.chromosome.startswith("chr")


@given(
    cdna=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=50).map(lambda s: "  " + s + "  "),
    )
)
def test_hgvs_cdna_whitespace_stripped(cdna: str | None) -> None:
    h = HGVS(cdna=cdna)
    if cdna is not None:
        assert h.cdna == cdna.strip()
    else:
        assert h.cdna is None
