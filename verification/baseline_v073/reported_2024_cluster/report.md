# Three-stage scenario report: `reported_2024_cluster`

All five sources using verified IREP 2024 emissions and source-specific capture assumptions.

| Headline metric | Result |
|---|---:|
| CO₂ captured | 2.860 Mt/y |
| CO₂ purified to pipeline specification | 2.845 Mt/y |
| CO₂ received at Port of Dunkerque | 2.845 Mt/y |
| Net CO₂ avoided within model boundary | 2.505 Mt/y |
| Three-stage CAPEX | €1.68 bn |
| Base levelized cost | €118.7/t received |
| Screening cost range | €72.9–164.5/t received |

## 1. Capture

Capture CAPEX: **€1.19 bn**. Annualized capture cost: **€89.5/t received**.

| ID | Source | Emissions basis (kt/y) | Captured (kt/y) | Technology | Capture rate | Availability |
|---|---|---:|---:|---|---:|---:|
| S1 | Chaux et Dolomies du Boulonnais | 603.0 | 533.3 | Cryocap FG cryogenic separation | 95.0% | 95.0% |
| S2 | ETEX France Building Performance | 44.8 | 30.8 | Post-combustion amine absorption | 90.0% | 90.0% |
| S3 | EQIOM Lumbres cement plant | 405.0 | 329.2 | Oxyfuel process with Cryocap Oxy separation | 92.0% | 93.0% |
| S4 | Aluminium Dunkerque | 492.0 | 266.6 | Low-concentration flue-gas amine capture | 85.0% | 85.0% |
| S5 | ArcelorMittal Dunkerque steelworks | 5,995.0 | 1,699.6 | DMX demixing-solvent absorption | 90.0% | 90.0% |

## 2. Purification

Purification CAPEX: **€253.2 m**. Annualized purification cost: **€21.0/t received**.

| ID | Captured feed (kt/y) | Product (kt/y) | Recovery | CO₂ purity | H₂O | Screened specification |
|---|---:|---:|---:|---:|---:|---|
| S1 | 533.3 | 530.7 | 99.5% | 99.99 mol-% | 20 ppmv | Pass |
| S2 | 30.8 | 30.7 | 99.5% | 99.90 mol-% | 20 ppmv | Pass |
| S3 | 329.2 | 327.5 | 99.5% | 99.95 mol-% | 20 ppmv | Pass |
| S4 | 266.6 | 265.3 | 99.5% | 99.90 mol-% | 20 ppmv | Pass |
| S5 | 1,699.6 | 1,691.1 | 99.5% | 99.90 mol-% | 20 ppmv | Pass |

## 3. Transport to the sink site

Pipeline CAPEX: **€238.8 m**. Annualized transport cost: **€8.2/t received**.

The optimized screening network contains 5 segments, totals 289.5 km, starts at 110 bar and reaches Dunkerque at no less than 87.8 bar.

Transport properties are calculated with the **Peng-Robinson equation of state** at 35.0 °C. PR density and compressibility are evaluated iteratively at the representative mean pressure of each segment.

Selected material screen: **Carbon steel X65 · reference**; calculated pipe steel **6.7 kt**; wall range **6.4–7.7 mm**.

| From | To | Route (km) | Flow (Mt/y) | Diameter | Wall (mm) | Density (kg/m³) | Z | Velocity (m/s) | ΔP (bar) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S4 | Sink | 8.6 | 1.956 | DN 250 | 7.7 | 678.3 | 0.2701 | 2.04 | 6.68 |
| S1 | Sink | 48.5 | 0.531 | DN 200 | 6.7 | 673.5 | 0.2689 | 0.87 | 9.11 |
| S3 | Sink | 45.3 | 0.358 | DN 150 | 6.4 | 654.9 | 0.2652 | 1.08 | 17.75 |
| S5 | S4 | 11.3 | 1.691 | DN 250 | 7.7 | 678.5 | 0.2701 | 1.76 | 6.55 |
| S2 | S3 | 175.8 | 0.031 | DN 100 | 6.4 | 682.5 | 0.2712 | 0.20 | 4.44 |

## 4. Environmental study

Assessment year: **2030**. The screening layer combines capture/purification energy emissions, direct pipeline leakage, and lifecycle transport factors based on annual tonne-kilometres.

| Environmental metric | Result |
|---|---:|
| Total electricity demand | 621.7 GWh/y |
| Capture steam demand | 5,520.0 TJ/y |
| Direct pipeline leakage | 166.5 t CO₂/y |
| Pipeline use-phase climate burden | 249.7 t CO₂-eq/y |
| Pipeline construction climate burden | 99.9 t CO₂-eq/y |
| Selected pipe-material embodied carbon | 14,601.9 t CO₂-eq total inventory |
| Annualized material delta versus X65 | 0.0 t CO₂-eq/y |
| Total modeled climate burden | 340,720.6 t CO₂-eq/y |
| Lifecycle net CO₂ avoided | 2.505 Mt/y |
| Climate burden intensity | 119.8 kg CO₂-eq/t received |
| Net avoidance efficiency | 88.0% |

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
