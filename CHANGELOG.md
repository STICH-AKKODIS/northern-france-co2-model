# Changelog

## 0.6.0 — 2026-10-21

- Added independent capture and purification technology selection for every active source, filtered by source sector.
- Added bounded controls for capture efficiency, purification recovery, CO₂ purity, H₂O, O₂, NOₓ, SOₓ and CO product targets.
- Added a shared technology catalogue used by both the calculation engine and the Streamlit interface, including feasible ranges, reference economics, utility intensities, maturity and hazard notes.
- Propagated target severity into source flow, scaled CAPEX/OPEX, electricity, steam, indirect emissions, product-quality screening and qualitative process-safety flags.
- Added flow-weighted product composition to the Peng–Robinson transport calculation and corrected hydraulic mass flow for the non-CO₂ fraction of lower-purity products.
- Kept out-of-spec configurations calculable for trade-off comparison while clearly flagging receiver-benchmark and phase-envelope review requirements.
- Added source-configuration tables to Capture, Purification and Decision lab views and new regression tests for independent technology selection, 95–98% capture, 95–99.95% purity and feasibility-range validation.

## 0.5.0 — 2026-09-29

- Added an executive scorecard with independent economics, hydraulic, capacity, evidence-maturity and product-quality decision gates.
- Added a transparent pipeline-material screen for X65, X70, X80, low-carbon X65 and 13Cr CRA, including pressure wall, steel mass, material-sensitive CAPEX and embodied carbon.
- Added a management Decision lab with cost-versus-carbon material comparison, CO₂-value headroom, indicative payback and ranked ±20% cost sensitivities.
- Preserved the X65 reference hydraulic and cost baseline; alternative materials retain the same optimized topology and hydraulic diameters for an understandable like-for-like comparison.
- Added regression tests for material mass/carbon reconciliation, low-carbon steel trade-offs and non-mutating custom material overrides.
