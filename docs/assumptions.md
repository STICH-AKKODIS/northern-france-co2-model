# Engineering basis, equations and uncertainty

## 1. Model boundary

The engineering chain contains three physical sections, with a fourth environmental-study layer in the dashboard:

1. **Capture** — separation of CO₂ from the selected industrial gas streams.
2. **Purification** — dehydration, impurity polishing and compression to the 110 bar pipeline inlet.
3. **Transport** — dense-phase pipeline collection to the supplied Port of Dunkerque coordinate `(636000, 7105000)` in Lambert-93 (`EPSG:2154`), using the Peng–Robinson equation of state for CO₂-mixture density and compressibility.
4. **Environmental study** — climate, energy-demand, direct leakage and transport lifecycle screening applied to the three-stage engineering result.

The calculation stops at arrival at that site. Liquefaction, buffer tanks, ship loading, shipping, injection, geological storage, monitoring and long-term liability are excluded. The public D’Artagnan capacities of 1.5 Mt/y initially and up to 4 Mt/y are used only as receiving constraints; no terminal cost or energy is included.

## 2. Scenario basis

| Scenario | Source basis | Selected sites | Dunkerque constraint |
|---|---|---|---:|
| `announced_2030` | Public project product flows | CalCC Réty and K6 Lumbres | 1.5 Mt/y |
| `reported_2024_cluster` | Official IREP 2024 total CO₂ | All five | 4.0 Mt/y |
| `user_inventory_4mt` | Original supplied table | All five | 4.0 Mt/y |
| `user_inventory_unconstrained` | Original supplied table | All five | Non-binding 12 Mt/y model ceiling |

The announced case is the recommended presentation case because the two flows are tied to named projects. The remaining non-project-backed capture systems are conceptual or pilot-derived.

## 3. Capture

For inventory-based cases:

`captured CO₂ = reported emissions × capturable fraction × capture rate × availability`

The capturable fraction represents the share of a multi-stack site that can practically be connected. Capture rate is the unit separation performance. Availability converts nameplate performance into an annual quantity. Keeping these terms separate prevents a 90% absorber rate from being applied automatically to an entire steel or aluminium site.

Technology mapping:

| ID | Site | Capture basis | Maturity |
|---|---|---|---|
| S1 | Réty lime | Cryocap FG; 95% capture supported by CalCC | Project-specific |
| S2 | Auneuil plaster | Post-combustion amine | Conceptual screening |
| S3 | Lumbres cement | Oxyfuel kiln plus Cryocap Oxy | Project plus screening |
| S4 | Aluminium Dunkerque | Low-concentration pot-gas amine capture | Low-maturity screening |
| S5 | ArcelorMittal Dunkerque | DMX on selected blast-furnace gas | Pilot plus screening |

Capture CAPEX is scaled as:

`capture CAPEX = reference CAPEX × (captured flow / reference flow)^0.67`

Annual capture cost includes annualized CAPEX, fixed O&M, electricity, steam and consumables. The 6% real discount rate and 25-year project life can be changed in the interface.

### 3.1 Interactive capture technology and efficiency

Each active source can use any capture technology whose `compatible_sectors` list in `config/technologies.toml` contains that source's sector. The catalogue currently contains Cryocap FG, post-combustion amine, oxyfuel/Cryocap Oxy, dilute-gas amine and DMX. Each option has its own reference capture rate, technically screened minimum/maximum rate, reference capacity, CAPEX, electricity, steam, consumables, fixed O&M, scale exponent, readiness and hazard note.

The model does not extrapolate outside the technology range. Within the range, target-dependent energy, CAPEX and variable-OPEX multipliers are piecewise-linear about the reference point:

`m(x) = m_min + (x − x_min)/(x_ref − x_min) × (1 − m_min), for x ≤ x_ref`

`m(x) = 1 + (x − x_ref)/(x_max − x_ref) × (m_max − 1), for x > x_ref`

The selected multiplier is applied to the technology's reference utility intensity or reference CAPEX before normal flow scaling. This makes a 98% capture target require more energy/capital than the same technology at its reference rate while preserving the published base-source results at their default settings. It is a transparent screening interpolation, not an absorber/stripper simulation.

## 4. Purification

`pipeline product = captured CO₂ × purification recovery`

The base recovery is 99.5%. The train represents water knockout, dehydration, source-appropriate polishing, non-condensable removal where needed and compression to 110 bar. Purification CAPEX is scaled independently from capture, and its electricity and consumables are reported separately.

Public project information generally reports integrated capture-project cost rather than a vendor split between separator and conditioning package. The model therefore divides each existing integrated reference into capture and purification blocks while preserving the original combined reference CAPEX:

| ID | Capture reference (€m) | Purification reference (€m) | Combined (€m) |
|---|---:|---:|---:|
| S1 | 160.0 | 38.444 | 198.444 |
| S2 | 145.0 | 35.0 | 180.0 |
| S3 | 240.0 | 60.0 | 300.0 |
| S4 | 330.0 | 70.0 | 400.0 |
| S5 | 750.0 | 150.0 | 900.0 |

This allocation is a transparent screening assumption, not a supplier quotation. The same principle is used to split the existing combined electricity and consumables assumptions, so the total utility basis is not increased by creating the separate stage.

### Product-quality screen

Six modeled components are checked against the 2025 Northern Lights liquid-CO₂ cargo benchmark:

| Component | Requirement |
|---|---:|
| CO₂ | ≥ 99.81 mol-% |
| H₂O | ≤ 30 ppm-mol |
| O₂ | ≤ 10 ppm-mol |
| NOₓ | ≤ 1.5 ppm-mol |
| SOₓ | ≤ 10 ppm-mol |
| CO | ≤ 100 ppm-mol |

The published benchmark contains 27 component or solids limits. The model therefore reports explicit coverage of `6 / 27` (22.2%) and lists the 21 unscreened components as **assay required**. It deliberately does not assume unmodeled species are zero. The Northern Lights cargo specification is an external reference, not a contractual Dunkerque pipeline acceptance specification. A complete compositional assay, interaction limits, material review and binding receiver specification are required before FEED.

The complete traceability table is in `data/co2_receiving_specification_reference.csv`.

Reference: https://norlights.com/wp-content/uploads/2025/06/Liquid-specification-2306251.pdf

### 4.1 Interactive purification technology and product targets

Each source can independently select molecular-sieve polishing, standard dehydration/polishing, cryogenic polishing, enhanced dehydration, non-condensable removal or a membrane-hybrid train. The selectable bounds in `config/technologies.toml` cover purification recovery, CO₂ molar purity, H₂O, O₂, NOₓ, SOₓ and CO. The component targets are checked for a physically coherent total composition and rejected if the stated CO₂ plus trace components exceeds 100 mol-%.

Purification energy, CAPEX and variable OPEX respond to a dimensionless separation-effort index:

`E = 0.45 P + 0.25 R + 0.20 D + 0.10 I`

where `P` is normalized CO₂-purity stringency, `R` is normalized recovery, `D` is normalized dryness stringency (lower H₂O is more severe), and `I` is the mean normalized removal stringency for O₂, NOₓ, SOₓ and CO. Every term is bounded between zero and one using that technology's minimum and maximum. Energy/CAPEX/OPEX multipliers are interpolated around the technology's reference effort with the same piecewise form used for capture.

A configuration that misses the six-component external quality benchmark remains calculable. This is deliberate: it allows a 95% and 99.5% product case to be compared economically and hydraulically. The result is marked `FAIL`, receives an Amber safety/quality flag, and is counted in the executive gate. It must not be interpreted as receiver acceptance.

The qualitative process-safety screen combines the selected technology's hazard category with water, oxygen, purity, receiver-quality and phase-envelope flags. It is an auditable screening status, not a quantitative risk assessment, HAZOP, LOPA or QRA.

## 5. Transport to Dunkerque

Every source/sink spanning tree without free junction nodes is evaluated. With five sources plus the sink, the complete Cayley set contains `6^(6-2) = 1,296` trees. Each candidate is oriented toward Dunkerque, branch flows are accumulated, standard diameters are selected and the least annualized-cost feasible topology is retained.

Straight-line Lambert-93 distances are multiplied by documented source-specific route factors from 1.10 to 1.35. These are early corridor allowances, not surveyed routes.

Hydraulic basis:

- 8,000 full-flow operating hours per year;
- inlet pressure 110 bar;
- minimum sink-arrival pressure 85 bar;
- maximum velocity 2.5 m/s;
- Peng–Robinson mixture EOS for density and compressibility at the segment representative pressure;
- transport temperature 35 °C;
- base EOS design composition: CO₂ 0.9992, N₂ 0.0005, O₂ 0.0001 and Ar 0.0002 mole fraction;
- for allocated sources, flow-weighted CO₂ and O₂ targets are used and the remaining dry-gas fraction is split between N₂ and Ar in the configured base ratio; the base composition is retained only when no source flow is allocated;
- classical quadratic mixing rule with binary interaction parameters `kij = 0`;
- screening viscosity `7×10⁻⁵ Pa·s`;
- carbon-steel roughness 0.045 mm;
- standard DN 100–600 candidates;
- Darcy–Weisbach pressure loss and Swamee–Jain friction factor;
- estimated leakage `0.02% per 100 km` of segment throughput.

Pipeline diameter is based on flow during the 8,000 operating hours, not a 365-day average. For each candidate diameter, PR density and Z are iterated at an estimated segment-mean pressure before Darcy–Weisbach loss is evaluated. Segments are upsized until every source-to-sink path satisfies both velocity and cumulative pressure-drop limits.

The source and sink ledgers remain expressed as tonnes of CO₂. For hydraulics, that CO₂ flow is divided by the PR mixture's CO₂ mass fraction to obtain total stream mass flow. This correction is material for lower-purity comparison cases and prevents a 95 mol-% product from being treated as if the whole transported stream were pure CO₂. Trace H₂O, NOₓ, SOₓ and CO are screened for quality/safety but are not separate PR components; they are included in the dry inert balance at this level. A detailed phase-envelope warning is raised for customized compositions that miss the external benchmark or fall below its CO₂ target.

The installed-cost correlation is anchored at €1.9 million/km for DN 300, scaled with diameter exponent 1.20. It includes a €5 million connection allowance per active source. A 2% fixed O&M factor is applied.

Reference: https://www.netl.doe.gov/projects/files/QualityGuidelinesforEnergySystemStudiesCarbonDioxideTransportandStorageCostsinNETLStudies_073124.pdf

### 5.1 Pipeline-material decision screen

The dashboard compares X65, X70, X80, low-carbon X65 and 13Cr corrosion-resistant alloy on the **same optimized topology and hydraulic internal diameters**. This isolates the first-order material trade-off and prevents network changes from obscuring the comparison.

The pressure wall is screened with the Barlow relation:

`t_pressure = P_design × D_internal / (2 × design factor × SMYS)`

The displayed wall is:

`t = max(t_pressure + corrosion allowance, 6.4 mm)`

The shared assumptions are 120 bar design pressure, 0.72 design factor and 7,850 kg/m³ steel density. X65, X70, X80 and low-carbon X65 use a 3 mm corrosion allowance; the indicative 13Cr case uses 1 mm. Pipe mass is calculated from the annular steel area and indicative route length.

The X65 installed-cost correlation is used as the reference. For alternatives, 35% of installed route CAPEX is treated as material-sensitive:

`CAPEX multiplier = 0.65 + 0.35 × (alternative steel mass / X65 steel mass) × relative material price`

The other 65% represents installation, civil works, route preparation and other costs not assumed to scale directly with pipe material. Embodied-carbon factors are screening values in t CO₂-eq/t steel. The environmental ledger adds only the alternative material's delta versus X65, annualized over project life, because the generic pipeline-construction factor already contains the baseline construction burden.

| Material option | SMYS (MPa) | Corrosion allowance (mm) | Relative material price | Embodied carbon (t CO₂-eq/t steel) | Status |
|---|---:|---:|---:|---:|---|
| X65 reference | 448 | 3 | 1.00 | 2.18 | Reference screen |
| X70 | 483 | 3 | 1.05 | 2.18 | Comparative screen |
| X80 | 552 | 3 | 1.12 | 2.18 | Comparative screen |
| Low-carbon X65 | 448 | 3 | 1.08 | 0.95 | Procurement scenario; supplier EPD required |
| 13Cr CRA | 450 | 1 | 2.40 | 4.50 | Indicative alternative; service suitability and supplier EPD required |

The X-grade SMYS values follow the standard grade designations used for line pipe. The 2.18 t CO₂-eq/t conventional-steel factor uses worldsteel's 2024 global average GHG intensity for crude steel as a screening anchor, not a product-specific line-pipe EPD. The price multipliers, low-carbon-steel factor and CRA factor are explicit scenario assumptions; replace them with supplier quotations and EN 15804/ISO 14025 product declarations before an investment decision.

This calculation is suitable for management sensitivity only. Final selection requires the applicable pipeline code and location class, validated CO₂ composition and water limit, decompression/fracture assessment, toughness, fatigue, corrosion and erosion studies, welding and inspection requirements, fittings and valves, procurement availability, route-specific loads, and supplier environmental product declarations.

Applicable design references for the next phase include ISO 27913:2024 and DNV-RP-F104. The latter specifically covers CO₂ properties, safety, design premises, materials, construction, operation and re-qualification; neither is replaced by the dashboard screen.

References:

- https://www.iso.org/standard/76676.html
- https://www.iso.org/standard/84840.html
- https://www.dnv.com/energy/standards-guidelines/dnv-rp-f104-design-and-operation-of-carbon-dioxide-pipelines/
- https://worldsteel.org/wider-sustainability/sustainability-indicators/

## 6. Cost and emissions accounting

Capital is annualized with:

`CRF = r(1+r)^n / ((1+r)^n - 1)`

The levelized three-stage cost is:

`(capture annual cost + purification annual cost + transport annual cost) / CO₂ received at Dunkerque`

No one-time CAPEX is added directly to annual OPEX. All costs are expressed on a 2026 euro basis. The base values are deterministic screening estimates.

Net avoided CO₂ within the boundary is:

`CO₂ received at Dunkerque − capture energy emissions − purification energy emissions`

Pipeline leakage is already deducted when calculating received CO₂. The engineering headline net-avoided metric remains operational. The separate environmental study adds screening pipeline operation/construction lifecycle factors and reports a lifecycle net-avoided metric; excluded downstream activities remain outside both boundaries.

## 7. Environmental study

The environmental layer is a screening assessment attached to every scenario. It reports annual capture and purification electricity, capture steam demand, direct pipeline leakage, and a transport lifecycle climate burden based on annual tonne-kilometres. The dense-pipeline use-phase factor is interpolated by assessment year from the existing project LCA trajectory; the default 2030 value is 3.0 g CO₂-eq/tkm. A separate 1.2 g CO₂-eq/tkm construction factor is included.

The environmental lifecycle net avoided CO₂ is:

`pipeline product − leakage − capture energy emissions − purification energy emissions − pipeline use-phase LCA − pipeline construction LCA − annualized material delta versus X65`

Alternative truck, barge and rail factors are included only as transport screening benchmarks. This is not an ISO-compliant project LCA. Biodiversity, land occupation, water impacts, crossings, local air quality, noise and construction disturbance require a routed corridor and project-specific inventories.

## 8. Uncertainty treatment

The dashboard range is a deterministic maturity range, not a statistical confidence interval:

- project-specific source: ±20%;
- project-plus-screening: ±30%;
- pilot-plus-screening: ±40%;
- conceptual screening: ±40%;
- low-maturity screening: ±50%;
- transport annual cost: ±35%.

This produces a more honest presentation than showing extra decimal places without reflecting project maturity. Public JRC studies report wide industrial capture-cost dispersion, approximately €40–235/t across the modeled EU facility set, with an average near €82/t in the 2026 bottom-up assessment.

References:

- https://publications.jrc.ec.europa.eu/repository/handle/JRC146193
- https://publications.jrc.ec.europa.eu/repository/handle/JRC139285

## 9. Required data for the next fidelity level

The highest-value improvements are:

1. stack-by-stack flow, hours, CO₂ concentration, pressure, temperature, moisture and complete impurity assays;
2. confirmed battery-limit conditions and vendor heat/mass balances for CalCC and K6;
3. vendor CAPEX/OPEX quotations and utility integration studies;
4. a binding pipeline receiver specification;
5. surveyed GIS corridors, exclusions, crossings, elevation and land costs;
6. calibrated binary interaction parameters, viscosity/thermal-property correlations, terrain heat transfer and transient multiphase hydraulics;
7. fracture-control, materials, relief/blowdown and operability studies.
