# Active model data

`source_inventory.csv` is the only source register used by the model. It contains:

- corrected installation identities and official Lambert-93 coordinates;
- original user-supplied emissions;
- verified IREP 2024 total and fossil CO₂;
- announced CalCC/K6 product flows;
- source-specific capture coverage, capture rate and availability;
- default capture and purification technology identifiers linked to `config/technologies.toml`;
- separate capture and purification energy, CAPEX and OPEX assumptions;
- purification recovery and screened product composition;
- route uplift, maturity and primary-source lineage.

The separate capture/purification references preserve the former combined reference CAPEX and total utility basis. Their allocation is documented in `docs/assumptions.md` and is intentionally visible for replacement when vendor data become available.

`co2_product_specification.csv` contains the six Northern Lights limits that can be screened with the available information. `co2_receiving_specification_reference.csv` records all 27 limits in the June 2025 public cargo benchmark and identifies which six are modeled. A passing result means only that the modeled subset passes. It does not imply acceptance of unmodeled trace species or compliance with a future Dunkerque pipeline contract.

`model_assumption_register.csv` is the auditable register of evidence class, uncertainty and FEED replacement actions for the principal technical and economic assumptions.

The model never edits these files while running. Dashboard selections and sensitivities are applied in memory.

`config/technologies.toml` is the single catalogue for selectable capture and purification technologies. It contains sector compatibility, technically screened operating ranges, reference cost/energy inputs, severity interpolation endpoints, technology readiness and qualitative hazard notes. The model rejects targets outside those ranges instead of extrapolating silently.
