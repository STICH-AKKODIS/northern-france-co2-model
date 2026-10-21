# Dashboard user guide

## Open the model

Double-click `START_MODEL.bat`. The first launch prepares the private model environment, then the dashboard opens in the default browser.

Keep the small model window open during the presentation. Close it when finished.

## Run a scenario

1. Choose a scenario in the left panel.
2. Under **Source technology & targets**, open any selected source. Choose its capture technology and efficiency independently, then choose its purification technology, recovery, CO₂ purity and H₂O target. Enable the advanced component control to set O₂, NOₓ, SOₓ and CO.
3. Optionally open **Economic sensitivity** and change electricity price, steam price, discount rate or project life.
4. Open **Management and pipeline choices** to select a material screen and the CO₂-value / avoided-cost threshold used for the management comparison.
5. Click **Run selected scenario**.
6. Wait for the scenario title and values to update.

Changing a control does not silently change the displayed results. The dashboard shows a message until **Run selected scenario** is clicked.

## Explain the result

Start with the three cards:

- **Capture** shows how much CO₂ is separated and its capture CAPEX/cost.
- **Purification** shows specification-compliant pipeline product and recovery.
- **Transport to sink** shows how much reaches Dunkerque, the network length and minimum pressure.

Read the **Executive decision gates**, then open the five tabs in order. The gates are independent: economics cannot compensate for an unresolved product-quality or hydraulic concern.

### Capture tab

Use the emissions-versus-captured chart to explain that whole-site emissions are not the same as capturable emissions. The table identifies technology, capture rate, availability, CAPEX and maturity.

### Purification tab

Use the feed/product metrics to explain the 99.5% recovery. The quality table covers six modeled components. State clearly that a complete vendor assay is still required.

The economics and transport calculation remains visible when a selected product misses the external benchmark so that alternatives can be compared. The row and executive gate are marked **FAIL/Amber**; this is not the same as receiver acceptance. Targets outside the selected technology's configured range are rejected rather than extrapolated.

### Transport tab

Hover over a pipeline segment to see route length, CO₂ flow, diameter, selected material, screened wall, Peng–Robinson density, compressibility factor, velocity and pressure drop. When product targets are changed, the dashboard builds a flow-weighted dry-gas composition and updates EOS density and hydraulics. The total stream mass used hydraulically includes the modeled non-CO₂ fraction. A phase-envelope warning identifies configurations that need detailed multicomponent verification. The map is an optimized screening topology, not a surveyed right-of-way.

### Environmental study tab

Use the climate-burden breakdown to separate capture energy, purification energy, direct pipeline leakage, pipeline operation and construction screening burdens. The transport benchmark compares pipeline tonne-kilometre intensity with truck, barge and rail screening factors. Treat these as decision-screening indicators, not a project-specific ISO LCA.

### Decision lab tab

Start with **Selected source configurations** to compare technology, capture, recovery, product quality, energy emissions, cost and safety status source by source. Then use the lower-left direction of the material chart to explain the cost/carbon trade-off. The material table reports wall, steel mass, material carbon, pipeline CAPEX, chain cost, annual value headroom and simple payback. The CO₂ value is a decision threshold, not guaranteed revenue. The sensitivity chart ranks the levelized-cost movement caused by a ±20% one-at-a-time change in electricity, steam and stage CAPEX assumptions.

The comparison retains the same optimized topology and hydraulic diameters for every material. Before selecting a grade, complete fracture/decompression, toughness, corrosion, impurity, welding, fatigue, fittings, route-class and applicable-code work during FEED.

## Interpret the uncertainty range

The base cost is the deterministic model result. The range reflects source maturity and ±35% transport uncertainty. It is not a probability interval.

For presentations:

- quote the base and range together;
- identify project-backed versus conceptual sources;
- do not call the route construction-ready;
- do not add shipping or storage conclusions, because they are outside the model.

## Download results

Each engineering tab provides a CSV download. The Environmental study tab provides its own CSV, and the Decision lab provides the full material comparison table. Command-line scenario outputs include `environmental_summary.csv`, `environmental_transport_benchmarks.csv` and `environmental_report.md`. The Transport tab also provides the full source audit and JSON summary for the selected case.

## Recommended starting statement

> This is a screening/pre-FEED decision model. It keeps capture, purification and Peng–Robinson pipeline transport separate, reconciles their mass and cost accounts, and adds an environmental climate/energy screening layer. The physical chain ends when CO₂ reaches the supplied Port of Dunkerque site.
