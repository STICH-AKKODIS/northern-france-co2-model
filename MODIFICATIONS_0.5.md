# Version 0.5 management-interface upgrade

Date: 2026-09-29

## Purpose

Version 0.5 prepares the Streamlit model for a management presentation without changing the physical scope: capture, purification and dense-phase pipeline transport to the supplied Dunkerque receiving point. The environmental layer remains a study of those three stages, not a fourth physical process.

## Added

- Executive KPIs for lifecycle CO₂ avoided, CAPEX, cost per tonne, CO₂-value headroom, receiving-capacity use and hydraulic pressure margin.
- Independent decision gates for economics, hydraulics, capacity utilization, source-evidence maturity and product-quality evidence.
- Pipeline-material options: X65 reference, X70, X80, low-carbon X65 and indicative 13Cr CRA.
- Barlow pressure-wall screening at 120 bar, material-specific SMYS and corrosion allowance, calculated steel mass, material-sensitive CAPEX and embodied carbon.
- A Decision lab containing a cost-versus-carbon chart, detailed material table, annual value headroom, indicative simple payback and a ranked ±20% cost-exposure chart.
- CSV export of the material decision table.
- Regression coverage for material calculations and non-mutating custom overrides.

## Preserved

- X65 remains the reference case for route CAPEX and material comparisons.
- Network enumeration, hydraulic diameters, Peng–Robinson density/compressibility, Darcy–Weisbach pressure loss and flow allocation are unchanged for the reference case.
- Capture and purification technology assignments are unchanged.
- The model boundary still ends at receipt at Dunkerque; shipping, injection and storage are excluded.

## Interpretation limits

The material screen holds topology and hydraulic diameters constant. It supports comparison and management discussion, not final grade selection. FEED must establish the applicable pipeline code, location class, impurity and water envelope, decompression/fracture behaviour, toughness, corrosion, fatigue, welding, inspection, fittings/valves, procurement, route loads and supplier-specific environmental product declarations.

The selected CO₂ value is an avoided-cost or strategic-value threshold. Annual value headroom and simple payback are not revenue forecasts and exclude tax, grants, construction phasing, financing structure and commercial contracts.
