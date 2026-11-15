# Three-stage scenario report: `reported_2024_cluster`

All five sources using verified IREP 2024 emissions and source-specific capture assumptions.

Calculation mode: **process linked**. Capture → purification connected: **True**. Purification → transport connected: **True**.

| Headline metric | Result |
|---|---:|
| CO₂ captured | 2.860 Mt/y |
| CO₂ purified to pipeline specification | 2.845 Mt/y |
| CO₂ received at Port of Dunkerque | 2.845 Mt/y |
| Net CO₂ avoided within model boundary | 2.467 Mt/y |
| Three-stage CAPEX | €1.69 bn |
| Base levelized cost | €113.8/t received |
| Screening cost range | €70.3–157.3/t received |

## 1. Capture

Capture CAPEX: **€1.19 bn**. Annualized capture cost: **€82.5/t received**.

| ID | Source | Emissions basis (kt/y) | Captured (kt/y) | Technology | Method | Capture rate | Availability |
|---|---|---:|---:|---|---|---:|---:|
| S1 | Chaux et Dolomies du Boulonnais | 603.0 | 533.3 | Cryocap FG cryogenic separation | process_linked | 95.0% | 95.0% |
| S2 | ETEX France Building Performance | 44.8 | 30.8 | Post-combustion amine absorption | process_linked | 90.0% | 90.0% |
| S3 | EQIOM Lumbres cement plant | 405.0 | 329.2 | Oxyfuel process with Cryocap Oxy separation | process_linked | 92.0% | 93.0% |
| S4 | Aluminium Dunkerque | 492.0 | 266.6 | Low-concentration flue-gas amine capture | process_linked | 85.0% | 85.0% |
| S5 | ArcelorMittal Dunkerque steelworks | 5,995.0 | 1,699.6 | DMX demixing-solvent absorption | process_linked | 90.0% | 90.0% |

## 2. Purification

Purification CAPEX: **€263.0 m**. Annualized purification cost: **€23.1/t received**.

| ID | Captured feed (kt/y) | Product (kt/y) | Recovery | Target / achieved CO₂ | Target / achieved H₂O | Method | Target benchmark | Achieved benchmark |
|---|---:|---:|---:|---:|---:|---|---|---|
| S1 | 533.3 | 530.7 | 99.5% | 99.99 / 99.99 mol-% | 20 / 20 ppmv | process_linked | Pass | Pass |
| S2 | 30.8 | 30.7 | 99.5% | 99.90 / 99.90 mol-% | 20 / 20 ppmv | process_linked | Pass | Pass |
| S3 | 329.2 | 327.5 | 99.5% | 99.95 / 99.95 mol-% | 20 / 20 ppmv | process_linked | Pass | Pass |
| S4 | 266.6 | 265.3 | 99.5% | 99.90 / 99.90 mol-% | 20 / 20 ppmv | process_linked | Pass | Pass |
| S5 | 1,699.6 | 1,691.1 | 99.5% | 99.90 / 99.95 mol-% | 20 / 20 ppmv | process_linked | Pass | Pass |

## 3. Transport to the sink site

Pipeline CAPEX: **€238.8 m**. Annualized transport cost: **€8.2/t received**.

The optimized screening network contains 5 segments, totals 289.5 km, starts at 110 bar and reaches Dunkerque at no less than 87.8 bar.

Transport properties are calculated with the **Peng-Robinson equation of state** at 35.0 °C. PR density and compressibility are evaluated iteratively at the representative mean pressure of each segment.

Selected material screen: **Carbon steel X65 · reference**; calculated pipe steel **6.7 kt**; wall range **6.4–7.7 mm**.

| From | To | Route (km) | Flow (Mt/y) | Diameter | Wall (mm) | Density (kg/m³) | Z | Velocity (m/s) | ΔP (bar) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S4 | Sink | 8.6 | 1.956 | DN 250 | 7.7 | 678.8 | 0.2699 | 2.04 | 6.67 |
| S1 | Sink | 48.5 | 0.531 | DN 200 | 6.7 | 674.1 | 0.2687 | 0.87 | 9.10 |
| S3 | Sink | 45.3 | 0.358 | DN 150 | 6.4 | 655.6 | 0.2649 | 1.07 | 17.72 |
| S5 | S4 | 11.3 | 1.691 | DN 250 | 7.7 | 679.1 | 0.2699 | 1.76 | 6.54 |
| S2 | S3 | 175.8 | 0.031 | DN 100 | 6.4 | 683.0 | 0.2710 | 0.20 | 4.44 |

## 4. Environmental study

Assessment year: **2030**. The layer combines process utility/consumable/equipment emissions, direct pipeline leakage, and lifecycle transport factors based on annual tonne-kilometres.

| Environmental metric | Result |
|---|---:|
| Total electricity demand | 594.9 GWh/y |
| Capture steam demand | 5,417.3 TJ/y |
| Capture cooling demand | 6,323.5 TJ/y |
| Purification thermal demand | 95.9 GWhth/y |
| Purification cooling demand | 387.9 GWhth/y |
| Process consumable/equipment climate burden | 21,582.7 t CO₂-eq/y |
| Direct pipeline leakage | 166.5 t CO₂/y |
| Pipeline use-phase climate burden | 249.7 t CO₂-eq/y |
| Pipeline construction climate burden | 99.9 t CO₂-eq/y |
| Selected pipe-material embodied carbon | 14,601.9 t CO₂-eq total inventory |
| Annualized material delta versus X65 | 0.0 t CO₂-eq/y |
| Total modeled climate burden | 378,416.0 t CO₂-eq/y |
| Lifecycle net CO₂ avoided | 2.467 Mt/y |
| Climate burden intensity | 133.0 kg CO₂-eq/t received |
| Net avoidance efficiency | 86.7% |

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
