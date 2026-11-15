# Three-stage scenario report: `user_inventory_unconstrained`

Diagnostic upper-bound using the original user emissions without a binding receiving-site constraint.

| Headline metric | Result |
|---|---:|
| CO₂ captured | 4.006 Mt/y |
| CO₂ purified to pipeline specification | 3.986 Mt/y |
| CO₂ received at Port of Dunkerque | 3.986 Mt/y |
| Net CO₂ avoided within model boundary | 3.476 Mt/y |
| Three-stage CAPEX | €2.16 bn |
| Base levelized cost | €114.7/t received |
| Screening cost range | €70.0–159.3/t received |

## 1. Capture

Capture CAPEX: **€1.50 bn**. Annualized capture cost: **€86.4/t received**.

| ID | Source | Emissions basis (kt/y) | Captured (kt/y) | Technology | Capture rate | Availability |
|---|---|---:|---:|---|---:|---:|
| S1 | Chaux et Dolomies du Boulonnais | 642.9 | 568.6 | Cryocap FG cryogenic separation | 95.0% | 95.0% |
| S2 | ETEX France Building Performance | 270.9 | 186.5 | Post-combustion amine absorption | 90.0% | 90.0% |
| S3 | EQIOM Lumbres cement plant | 483.7 | 393.2 | Oxyfuel process with Cryocap Oxy separation | 92.0% | 93.0% |
| S4 | Aluminium Dunkerque | 616.4 | 334.0 | Low-concentration flue-gas amine capture | 85.0% | 85.0% |
| S5 | ArcelorMittal Dunkerque steelworks | 8,901.6 | 2,523.6 | DMX demixing-solvent absorption | 90.0% | 90.0% |

## 2. Purification

Purification CAPEX: **€319.7 m**. Annualized purification cost: **€19.9/t received**.

| ID | Captured feed (kt/y) | Product (kt/y) | Recovery | CO₂ purity | H₂O | Screened specification |
|---|---:|---:|---:|---:|---:|---|
| S1 | 568.6 | 565.8 | 99.5% | 99.99 mol-% | 20 ppmv | Pass |
| S2 | 186.5 | 185.6 | 99.5% | 99.90 mol-% | 20 ppmv | Pass |
| S3 | 393.2 | 391.2 | 99.5% | 99.95 mol-% | 20 ppmv | Pass |
| S4 | 334.0 | 332.3 | 99.5% | 99.90 mol-% | 20 ppmv | Pass |
| S5 | 2,523.6 | 2,511.0 | 99.5% | 99.90 mol-% | 20 ppmv | Pass |

## 3. Transport to the sink site

Pipeline CAPEX: **€339.6 m**. Annualized transport cost: **€8.4/t received**.

The optimized screening network contains 5 segments, totals 334.6 km, starts at 110 bar and reaches Dunkerque at no less than 85.5 bar.

Transport properties are calculated with the **Peng-Robinson equation of state** at 35.0 °C. PR density and compressibility are evaluated iteratively at the representative mean pressure of each segment.

Selected material screen: **Carbon steel X65 · reference**; calculated pipe steel **9.5 kt**; wall range **6.4–8.6 mm**.

| From | To | Route (km) | Flow (Mt/y) | Diameter | Wall (mm) | Density (kg/m³) | Z | Velocity (m/s) | ΔP (bar) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S4 | Sink | 8.6 | 2.843 | DN 300 | 8.6 | 680.5 | 0.2707 | 2.05 | 5.45 |
| S1 | Sink | 48.5 | 0.566 | DN 200 | 6.7 | 670.8 | 0.2683 | 0.93 | 10.37 |
| S3 | Sink | 45.3 | 0.391 | DN 150 | 6.4 | 646.1 | 0.2640 | 1.19 | 21.40 |
| S2 | Sink | 221.0 | 0.186 | DN 150 | 6.4 | 638.1 | 0.2631 | 0.57 | 24.49 |
| S5 | S4 | 11.3 | 2.511 | DN 300 | 8.6 | 680.3 | 0.2706 | 1.81 | 5.58 |

## 4. Environmental study

Assessment year: **2030**. The screening layer combines capture/purification energy emissions, direct pipeline leakage, and lifecycle transport factors based on annual tonne-kilometres.

| Environmental metric | Result |
|---|---:|
| Total electricity demand | 809.7 GWh/y |
| Capture steam demand | 8,379.5 TJ/y |
| Direct pipeline leakage | 277.8 t CO₂/y |
| Pipeline use-phase climate burden | 416.7 t CO₂-eq/y |
| Pipeline construction climate burden | 166.7 t CO₂-eq/y |
| Selected pipe-material embodied carbon | 20,777.5 t CO₂-eq total inventory |
| Annualized material delta versus X65 | 0.0 t CO₂-eq/y |
| Total modeled climate burden | 510,596.5 t CO₂-eq/y |
| Lifecycle net CO₂ avoided | 3.475 Mt/y |
| Climate burden intensity | 128.1 kg CO₂-eq/t received |
| Net avoidance efficiency | 87.2% |

### Transport climate benchmark

| Alternative mode | Mode intensity (g CO₂-eq/tkm) | Pipeline incl. construction | Pipeline reduction |
|---|---:|---:|---:|
| Truck (diesel) | 148.5 | 4.2 | 97.2% |
| Truck (electric) | 139.5 | 4.2 | 97.0% |
| Truck (H2) | 144.0 | 4.2 | 97.1% |
| Barge (diesel) | 88.2 | 4.2 | 95.2% |
| Train (electric) | 64.8 | 4.2 | 93.5% |

**Environmental scope note.** This is a screening climate/energy study, not an ISO-compliant project LCA. A routed corridor is required before quantifying biodiversity, land occupation, water, crossings, construction disturbance, noise or local air-quality impacts.

---

**Model boundary.** The calculation ends when pipeline-quality CO₂ reaches the Port of Dunkerque coordinates supplied for this study. Liquefaction, buffer storage, ship loading, shipping, geological injection and storage are excluded.

**Precision statement.** Results are deterministic screening estimates in 2026 euros. The displayed range applies maturity-based uncertainty to capture/purification costs and ±35% to routed pipeline cost; it is not a statistical confidence interval. Six product components are screened, but a complete vendor assay and receiving specification are required before FEED.
