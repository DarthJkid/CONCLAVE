"""CONCLAVE Streamlit UI — variant interpretation dashboard."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="CONCLAVE",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🧬 CONCLAVE")
    st.caption("Calibrated multi-agent variant interpretation")
    st.divider()

    genome_build = st.selectbox("Genome Build", ["GRCh38", "GRCh37"])
    st.divider()
    st.markdown("**Resources**")
    st.markdown("- [ACMG/AMP Guidelines](https://www.acmg.net)")
    st.markdown("- [gnomAD](https://gnomad.broadinstitute.org)")
    st.markdown("- [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar)")

# ── Main content ──────────────────────────────────────────────────────────────
st.title("🧬 CONCLAVE Variant Interpreter")
st.caption(
    "Calibrated Orchestrated Network of Criterion-level LLM Agents for Variant Evaluation"
)

with st.expander("ℹ️ About CONCLAVE", expanded=False):
    st.markdown(
        """
        CONCLAVE is a research-grade clinical genomics platform for **ACMG/AMP-aligned**
        variant interpretation featuring:
        - **Per-criterion LLM agents** with structured outputs
        - **Conformal abstention** — the system says "I don't know" when uncertain
        - **Full evidence provenance** — every decision is traceable
        - **Multi-agent orchestration** — 28 criterion agents working in parallel
        """
    )

st.divider()

# ── Variant input form ────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Variant Input")
    variant_tab, hgvs_tab = st.tabs(["Genomic Coordinates", "HGVS Notation"])

    with variant_tab:
        chrom = st.text_input("Chromosome", placeholder="13")
        pos_col, ref_col, alt_col = st.columns(3)
        with pos_col:
            position = st.number_input("Position (1-based)", min_value=1, value=32339461)
        with ref_col:
            ref = st.text_input("Reference Allele", placeholder="A")
        with alt_col:
            alt = st.text_input("Alternate Allele", placeholder="-")

    with hgvs_tab:
        cdna = st.text_input("cDNA notation", placeholder="NM_000059.4:c.5946delT")
        protein = st.text_input("Protein notation", placeholder="NP_000050.3:p.Ser1982fs")

with col2:
    st.subheader("Gene Context")
    gene = st.text_input("Gene Symbol", placeholder="BRCA2")
    inheritance = st.multiselect(
        "Inheritance Mode",
        ["autosomal_dominant", "autosomal_recessive", "X-linked", "mitochondrial"],
    )

st.divider()

# ── Run button ────────────────────────────────────────────────────────────────
run_col, _, status_col = st.columns([1, 2, 1])
with run_col:
    run_clicked = st.button("🚀 Interpret Variant", type="primary", use_container_width=True)
with status_col:
    st.caption(f"Build: **{genome_build}**")

if run_clicked:
    if not chrom or not ref or not alt:
        st.error("Please provide chromosome, reference allele, and alternate allele.")
    else:
        with st.spinner("Running CONCLAVE multi-agent pipeline…"):
            st.warning(
                "⚠️ Full pipeline not yet implemented — this is a UI scaffold. "
                "Connect `conclave.orchestrator` to enable live interpretation."
            )

        st.subheader("📋 Results")
        result_cols = st.columns(3)
        with result_cols[0]:
            st.metric("Classification", "VUS", delta=None)
        with result_cols[1]:
            st.metric("P(Pathogenic)", "—", delta=None)
        with result_cols[2]:
            st.metric("Criteria Met", "—", delta=None)
