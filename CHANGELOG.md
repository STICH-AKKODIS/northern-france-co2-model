# Changelog

## 0.8.0 — 15 November 2026

- Added a selectable process-linked calculation path while preserving the exact v0.7.3 coefficient screen as a regression baseline.
- Connected capture to purification with wet-product CO₂ flow, component composition, temperature and pressure; connected the achieved purification product to Peng–Robinson transport properties.
- Added MEA cyclic-capacity, reboiler, blower, pump, O₂/SOₓ degradation, solvent makeup and wet-product calculations, restricted to MEA-family technologies.
- Added separate Cryocap, oxyfuel, DMX, membrane, non-condensable-removal and cryogenic process-family responses.
- Added component-resolved purification, bulk-water knockout, residual dehydration, deoxygenation, refrigeration and multistage compression to 110 bar, with explicit heat, cooling, consumables and mass-balance diagnostics.
- Prevented physically inconsistent product targets from creating unaccounted inert gas; the achieved composition and a visible feasibility flag are now reported.
- Added configurable source-feed compositions and Streamlit controls for CO₂, H₂O, O₂, SOₓ, NOₓ and CO.
- Added process-consumable and annualized-equipment environmental burdens without changing the pipeline construction/material boundary.
- Added local read-only Papa-model runner, matched-input comparison script, comparison CSV/JSON/figure/report, method documentation and a 20-item improvement register.
- Added nine process-model tests; all 46 model, UI, EOS, trajectory and integration tests pass locally.

## 0.7.3 — 10 November 2026

- Fixed a Streamlit dashboard smoke-test bug: `AppTest` information alerts use `.value`, not `.message`.
- Made the CSV-import panel contract test independent of Streamlit while keeping interactive UI smoke checks when Streamlit is installed.
- UI tests now skip with an installation hint when Streamlit is unavailable, instead of failing during test collection.
- No changes to QGIS CSV formats, elevation fallback, hydraulic calculations, or the user workflow.

## 0.7.2 — 10 November 2026

- Added automatic QGIS 3D CSV import: reads `Z` or compatible elevation columns (metres) alongside the existing X/Y vertex format, with 0 m when Z is missing/NULL.
- Preserves imported Z through geometry ordering, multipart routes, source-based orientation, preview, JSON export, and hydraulic model calculations (3D lengths and elevation pressure changes).
- The source uses its CSV endpoint elevation; sink elevation comes from a route ending at the sink (otherwise 0 m). Conflicting shared-sink elevations cannot be applied.
- Updated trajectory panel to report elevation availability and per-route Z range, display Z on route hover, and explain missing-elevation assumptions.
- Added tests for 2D/3D, NULL Z, invalid elevations, multipart geometry and reversed routes.

## 0.7.1 — 2026-11-10

- Replaced manual trajectory coordinate tables with direct multi-file CSV upload using the QGIS `X,Y,id,Rety_Lumbr,vertex_index,vertex_part,vertex_part_index,distance,angle` format.
- Added route-ID grouping, ordered multipart parsing, proximity-based source suggestions, source assignment checks and a coordinate-accurate route preview.
- Added automatic route orientation, optional shared downstream connections, route cost status and visible straight-connector/multipart warnings requiring acknowledgement.
- Uses an explicit zero-elevation assumption because imported CSVs have no Z column; old automatic network remains available.
- Added CSV parser tests and updated the user guide.

## 0.7.0 — 2026-11-10

- Added a dedicated **Pipeline trajectory** panel with a paste-friendly, dynamic Lambert-93 X/Y/Z coordinate editor for every selected source.
- Added source-route endpoints at either the Dunkerque sink or a selected source/via point on another route, including connection-point validation, cycle rejection and automatic aggregation of shared downstream flows.
- Added 3D segment lengths, elevation static head, segment pressure ranges, minimum-network-pressure and maximum-design-pressure checks to the Peng–Robinson/Darcy hydraulic calculation.
- Added a per-route new/existing switch. Existing routes retain physical flow, hydraulic, leakage and use-phase LCA effects while project construction CAPEX, fixed O&M, source connection allowance, new-steel inventory and construction LCA are set to zero.
- Propagated trajectory changes into diameter selection, cost, material comparison, leakage, tonne-kilometres, environmental burdens, maps, KPI cards, downloads and decision indicators.
- Preserved the v0.6 automatically optimized network as the default comparison mode.

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
