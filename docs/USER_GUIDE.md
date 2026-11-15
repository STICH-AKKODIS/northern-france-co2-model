# Dashboard user guide

## Open the model

Double-click `START_MODEL.bat`. The first launch prepares the private model environment, then the dashboard opens in the default browser.

Keep the small model window open during the presentation. Close it when finished.

## Run a scenario

1. Choose a scenario in the left panel.
2. Choose **Process-linked engineering model** for v0.8.0, or **Legacy screening coefficients** for an exact v0.7.3 comparison.
3. Under **Source technology & targets**, open any selected source. Choose its capture technology and efficiency independently, then choose its purification technology, recovery, CO₂ purity and H₂O target. Enable advanced controls for product O₂, NOₓ, SOₓ and CO. In process-linked mode, **Adjust capture-feed composition** exposes source CO₂, H₂O, O₂, SOₓ, NOₓ and CO.
4. Optionally open **Economic sensitivity** and change electricity price, steam price, discount rate or project life.
5. Open **Management and pipeline choices** to select a material screen and the CO₂-value / avoided-cost threshold used for the management comparison.
6. Open **Pipeline trajectory** and upload one or more QGIS vertex CSVs. The importer detects multiple routes by `id`, sorts their vertices and displays a preview.
7. Assign each active CO₂ source to one imported route. Optionally, connect a route to a downstream route and mark existing assets (exclude their construction cost). Review any straight-line connector or multipart warnings and confirm.
8. Click **Apply imported trajectories and run**. Use **Run selected scenario** to recalculate the currently applied network, or **Use automatic network** to return to the original optimization.
9. Wait for the scenario title and values to update.

Changing a control does not silently change the displayed results. The dashboard shows a message until **Run selected scenario** is clicked.

## Explain the result

Start with the three cards:

- **Capture** shows how much CO₂ is separated, the method, utilities, solvent makeup, wet-product quality and capture CAPEX/cost.
- **Purification** shows the connected wet feed, recovery loss, achieved product, compression/heat/cooling and conditioning cost.
- **Transport to sink** shows how much reaches Dunkerque, the network length and minimum pressure.

Read the **Executive decision gates**, then open the six tabs in order. The gates are independent: economics cannot compensate for an unresolved product-quality or hydraulic concern.

### Capture tab

Use the emissions-versus-captured chart to explain that whole-site emissions are not the same as capturable emissions. The table identifies technology, capture rate, availability, CAPEX and maturity.

### Purification tab

Use the feed/product metrics to explain recovery. Open **Connected stage handoff and balance checks** to show that the capture wet product is the purification inlet and the achieved purification product is the pipeline feed. The quality table covers six modeled components.

The economics and transport calculation remains visible when a selected product misses the external benchmark so that alternatives can be compared. The row and executive gate are marked **FAIL/Amber**. If purity and trace targets cannot be formed from the available feed, the process-linked model reports the achievable product rather than inventing inert gas and adds a feasibility flag. Targets outside the selected technology's configured range are rejected rather than extrapolated.

### Pipeline trajectory tab

Upload CSV files with the same columns as `Route_Energie1.csv`: `X,Y,id,Rety_Lumbr,vertex_index,vertex_part,vertex_part_index,distance,angle`. X/Y must be Lambert-93 metres (`EPSG:2154`). Each distinct `id` becomes a route, even when several routes share a CSV. Multipart geometries are preserved in the preview; their successive parts are linked by straight segments in the hydraulic model, with a warning. The importer automatically proposes a source when its coordinates are within 5 km of a route end; confirm all assignments. Route orientation is corrected automatically to begin closest to the assigned source. For merging routes, choose the downstream source route and the closest vertex is selected as the junction. When the CSV includes QGIS **Z** (or an elevation field such as `z_m`, `elevation`, `altitude`), values in metres are imported automatically; when Z is absent or NULL, that vertex defaults to **0 m**. The source node uses the imported first-point Z. The sink node uses an imported last-point Z when the route ends exactly at the sink, otherwise Z = 0 m. Imported elevation changes affect 3D lengths and hydrostatic pressure. Any source or sink gap is filled by an explicit straight connector; its length appears in the preview summary. Such connectors are screening assumptions, not surveyed alignments.

Connections must be acyclic and every route must ultimately reach Dunkerque. When two routes merge, the downstream segment carries their combined flow. The **existing** option does not remove the asset physically: length, elevation, velocity, pressure change, leakage and use-phase environmental burden remain. It removes construction CAPEX, fixed O&M, the source-connection allowance, new-project steel and construction LCA for that route.

### Transport tab

Hover over a pipeline segment to see route length, elevation change, CO₂ flow, diameter, selected material, screened wall, Peng–Robinson density, velocity, friction loss, static head and net pressure change. New/costed routes are orange; existing/construction-excluded routes are dashed grey. When product targets are changed, the dashboard builds a flow-weighted dry-gas composition and updates EOS density and hydraulics. The total stream mass used hydraulically includes the modeled non-CO₂ fraction. A phase-envelope warning identifies configurations that need detailed multicomponent verification. In automatic mode the map is an optimized screening topology; in trajectory mode it follows the coordinates supplied by the user.

### Environmental study tab

Use the climate-burden breakdown to separate capture energy, purification energy, direct pipeline leakage, pipeline operation and construction screening burdens. The transport benchmark compares pipeline tonne-kilometre intensity with truck, barge and rail screening factors. Treat these as decision-screening indicators, not a project-specific ISO LCA.

### Decision lab tab

Start with **Selected source configurations** to compare technology, capture, recovery, product quality, energy emissions, cost and safety status source by source. Then use the lower-left direction of the material chart to explain the cost/carbon trade-off. The material table reports wall, steel mass, material carbon, pipeline CAPEX, chain cost, annual value headroom and simple payback. The CO₂ value is a decision threshold, not guaranteed revenue. The sensitivity chart ranks the levelized-cost movement caused by a ±20% one-at-a-time change in electricity, steam and stage CAPEX assumptions.

The comparison retains the selected topology and hydraulic diameters for every material and applies only to new/costed segments. Before selecting a grade, complete fracture/decompression, toughness, corrosion, impurity, welding, fatigue, fittings, route-class and applicable-code work during FEED.

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

> This is a process-linked engineering/pre-FEED decision model with a selectable legacy screen. It transmits flow and composition between capture, purification and Peng–Robinson pipeline transport, reconciles mass, energy and cost, and adds an environmental climate/energy layer. The physical chain ends when CO₂ reaches the supplied Port of Dunkerque site.
